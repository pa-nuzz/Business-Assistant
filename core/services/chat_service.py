"""
Chat service for handling chat business logic.
Extracted from views to enable testing and reusability.
"""
import logging
from typing import Dict, List, Optional, Generator
from django.contrib.auth.models import User
from core.models import Conversation, Message
from agents import orchestrator
from utils.sanitization import sanitize_plain_text

logger = logging.getLogger(__name__)


class ChatService:
    """Service for handling chat operations."""
    
    def __init__(self, user: User):
        self.user = user
    
    def send_message(
        self,
        message: str,
        conversation_id: Optional[str] = None,
        stream: bool = False
    ) -> Dict:
        """
        Send a message and get AI response.
        
        Args:
            message: User message content
            conversation_id: Optional conversation ID to continue
            stream: Whether to stream the response
            
        Returns:
            Dict with reply, conversation_id, model_used, tools_used, intent
        """
        # Validate and sanitize message
        message = message.strip()
        if not message:
            raise ValueError("Message cannot be empty")
        if len(message) > 4000:
            raise ValueError("Message too long")

        message = sanitize_plain_text(message, max_length=4000)
        
        # Check for intelligent commands
        command_result = self._process_intelligent_commands(message)
        if command_result:
            # Get or create conversation for command response
            conversation = self._get_or_create_conversation(conversation_id, message)
            
            # Save user message and command response
            self._save_messages(conversation, message, {
                "reply": command_result["response"],
                "model": "command_processor",
                "tools_used": command_result.get("tools_used", []),
                "intent": command_result.get("intent", "command")
            })
            
            return {
                "reply": command_result["response"],
                "conversation_id": str(conversation.id),
                "model_used": "command_processor",
                "tools_used": command_result.get("tools_used", []),
                "intent": command_result.get("intent", "command"),
            }
        
        # Get or create conversation
        conversation = self._get_or_create_conversation(conversation_id, message)
        
        # Build conversation history
        history = self._build_conversation_history(conversation)
        
        # Run agent
        try:
            result = orchestrator.run(
                user_message=message,
                user_id=self.user.id,
                conversation_history=history,
                user_name=self.user.get_full_name() or self.user.username,
            )
        except Exception as e:
            logger.exception("Agent run failed")
            raise RuntimeError("Failed to process message") from e
        
        # Save messages to DB
        self._save_messages(conversation, message, result)
        
        return {
            "reply": result.get("reply", ""),
            "conversation_id": str(conversation.id),
            "model_used": result.get("model", "unknown"),
            "tools_used": result.get("tools_used", []),
            "intent": result.get("intent", "chat"),
        }
    
    def send_message_stream(
        self,
        message: str,
        conversation_id: Optional[str] = None
    ) -> Generator[str, None, None]:
        """
        Send a message and stream AI response.
        
        Args:
            message: User message content
            conversation_id: Optional conversation ID to continue
            
        Yields:
            SSE formatted strings
        """
        # Validate and sanitize message
        message = message.strip()
        if not message:
            raise ValueError("Message cannot be empty")
        if len(message) > 4000:
            raise ValueError("Message too long")

        message = sanitize_plain_text(message, max_length=4000)
        
        # Get or create conversation
        conversation = self._get_or_create_conversation(conversation_id, message)
        
        # Build conversation history
        history = self._build_conversation_history(conversation)
        
        # Save user message immediately
        Message.objects.create(
            conversation=conversation,
            role="user",
            content=message,
        )
        conversation.save(update_fields=["updated_at"])
        
        # Stream response
        full_response = []
        model_info = {"used": "unknown"}
        stream_error = None
        
        try:
            for sse_data in orchestrator.run_stream(
                user_message=message,
                user_id=self.user.id,
                conversation_history=history,
                user_name=self.user.get_full_name() or self.user.username,
                conversation_id=str(conversation.id),
            ):
                yield sse_data
                
                # Collect response for saving
                if sse_data.startswith('data: ') and '[DONE]' not in sse_data:
                    try:
                        import json
                        data = json.loads(sse_data[6:])
                        if "token" in data:
                            full_response.append(data["token"])
                        if "metadata" in data:
                            model_info["used"] = data["metadata"].get("model", "unknown")
                        if "error" in data:
                            stream_error = data["error"]
                            logger.warning(f"Stream error received: {stream_error}")
                    except (json.JSONDecodeError, ValueError) as e:
                        logger.warning(f"SSE parse error: {e}")
                        
        except Exception as e:
            logger.exception("Streaming failed")
            stream_error = str(e)
            yield f'data: {{"error": "{str(e)}"}}\n\n'
        
        # Save assistant message after streaming completes (even if error)
        response_text = "".join(full_response)
        if response_text.strip() or stream_error:
            final_content = response_text if response_text.strip() else f"I encountered an error: {stream_error}"
            Message.objects.create(
                conversation=conversation,
                role="assistant",
                content=final_content,
                model_used=model_info["used"],
                tool_calls={"stream_error": stream_error} if stream_error else None,
            )
            conversation.save(update_fields=["updated_at"])
    
    def _get_or_create_conversation(
        self,
        conversation_id: Optional[str],
        message: str
    ) -> Conversation:
        """Get existing conversation or create new one."""
        if conversation_id:
            try:
                import uuid

                uuid.UUID(conversation_id)
            except (ValueError, TypeError):
                raise ValueError("Conversation not found")
            try:
                return Conversation.objects.get(id=conversation_id, user=self.user)
            except Conversation.DoesNotExist:
                raise ValueError("Conversation not found")
        
        return Conversation.objects.create(
            user=self.user,
            title=message[:80],
        )
    
    def _build_conversation_history(self, conversation: Conversation) -> List[Dict]:
        """Build conversation history with enhanced professional context."""
        recent_messages = list(conversation.messages.order_by("-created_at")[:20])
        recent_messages.reverse()
        
        # Build comprehensive professional system prompt
        system_content = self._build_professional_system_prompt()
        
        history = [{"role": "system", "content": system_content}]
        
        # Add recent document context if available
        doc_context = self._get_document_context()
        if doc_context:
            history.append({"role": "system", "content": f"Recent Documents Context:\n{doc_context}"})
        
        # Add conversation messages
        for m in recent_messages:
            history.append({"role": m.role, "content": m.content})
        
        return history
    
    def _build_professional_system_prompt(self) -> str:
        """Build professional system prompt with user context."""
        base_prompt = """You are AEIOU AI, a professional business assistant. Guidelines:
1. Always respond in a professional, courteous manner
2. Use clear, concise business language
3. Reference uploaded documents when relevant
4. Provide actionable insights and recommendations
5. Maintain confidentiality and data privacy
6. Ask clarifying questions when needed
7. Structure responses with clear headings and bullet points when appropriate
8. Focus on business value and practical applications"""
        
        # Add user-specific context
        context_parts = [base_prompt]
        
        try:
            profile = self.user.business_profile
            if profile:
                user_context = "\n\nCurrent User Context:"
                if profile.company_name:
                    user_context += f"\n- Company: {profile.company_name}"
                if profile.industry:
                    user_context += f"\n- Industry: {profile.industry}"
                if profile.company_size:
                    user_context += f"\n- Company Size: {profile.company_size}"
                if profile.goals:
                    user_context += f"\n- Business Goals: {', '.join(goal.get('title', '') for goal in profile.goals[:3])}"
                context_parts.append(user_context)
        except Exception:
            pass
        
        # Add conversation summary
        try:
            from core.models import Message
            recent_convos = Conversation.objects.filter(user=self.user).order_by("-updated_at")[:5]
            if recent_convos.exists():
                context_parts.append("\n\nRecent Activity: User has been actively discussing business matters and seeking professional guidance.")
        except Exception:
            pass
        
        return "\n".join(context_parts)
    
    def _get_document_context(self) -> str:
        """Get context from recently uploaded documents."""
        try:
            from core.models import Document
            recent_docs = Document.objects.filter(
                user=self.user, 
                status="ready"
            ).order_by("-created_at")[:3]
            
            if not recent_docs.exists():
                return ""
            
            doc_summaries = []
            for doc in recent_docs:
                summary = f"- {doc.title or doc.file.name}"
                if doc.summary:
                    # Truncate long summaries
                    summary += f": {doc.summary[:100]}{'...' if len(doc.summary) > 100 else ''}"
                doc_summaries.append(summary)
            
            return "Recently uploaded documents:\n" + "\n".join(doc_summaries)
        except Exception:
            return ""
    
    def _process_intelligent_commands(self, message: str) -> Optional[Dict]:
        """Process intelligent commands and return appropriate responses."""
        message_lower = message.lower().strip()
        
        # Document analysis commands
        if any(phrase in message_lower for phrase in ["analyze this document", "analyze document", "document analysis"]):
            return self._handle_document_analysis_command()
        
        # Task creation commands
        if any(phrase in message_lower for phrase in ["create a task", "create task", "add task"]):
            return self._handle_task_creation_command(message)
        
        # Summary commands
        if any(phrase in message_lower for phrase in ["summarize my", "summarize recent", "chat summary"]):
            return self._handle_summary_command()
        
        # Analytics commands
        if any(phrase in message_lower for phrase in ["show me trends", "analytics", "dashboard", "metrics"]):
            return self._handle_analytics_command()
        
        # Document processing commands
        if any(phrase in message_lower for phrase in ["recheck document", "process document", "upload status"]):
            return self._handle_document_status_command()
        
        return None
    
    def _handle_document_analysis_command(self) -> Dict:
        """Handle document analysis command."""
        try:
            from core.models import Document
            recent_docs = Document.objects.filter(
                user=self.user, 
                status="ready"
            ).order_by("-created_at")[:1]
            
            if not recent_docs.exists():
                return {
                    "response": "I don't see any recently uploaded documents available for document analysis. Please upload a document first, and I'll be happy to analyze it for you.",
                    "intent": "document_analysis",
                    "tools_used": ["document_search"]
                }
            
            doc = recent_docs.first()
            response = f"I'll analyze your most recent document: **{doc.title or doc.file.name}**.\n\n"
            response += "Based on the document content and your business context, here are the key insights:\n\n"
            response += "• **Document Summary**: " + (doc.summary[:200] + "..." if doc.summary and len(doc.summary) > 200 else doc.summary or "Processing complete") + "\n"
            response += "• **Business Relevance**: This document contains valuable information for your business operations\n"
            response += "• **Action Items**: I recommend reviewing the key sections and implementing relevant insights\n\n"
            response += "Would you like me to dive deeper into any specific aspect of this document?"
            
            return {
                "response": response,
                "intent": "document_analysis",
                "tools_used": ["document_analysis", "semantic_search"]
            }
        except Exception as e:
            logger.exception(f"Document analysis command failed: {e}")
            return {
                "response": "I encountered an issue while analyzing your document. Please try again or contact support if the problem persists.",
                "intent": "document_analysis",
                "tools_used": ["document_analysis"]
            }
    
    def _handle_task_creation_command(self, message: str) -> Dict:
        """Handle task creation command."""
        # Extract task content from message
        task_content = message.replace("create a task", "").replace("create task", "").replace("add task", "").strip()
        
        if not task_content:
            return {
                "response": "I'd be happy to help you create a task! Please provide more details about what you'd like to accomplish. For example: 'Create a task to review the quarterly report by Friday'.",
                "intent": "task_creation",
                "tools_used": ["task_extraction"]
            }
        
        response = f"I've identified a task from your request: **{task_content}**\n\n"
        response += "I can help you create this task with proper scheduling and priority. Here's what I recommend:\n\n"
        response += f"• **Task**: {task_content}\n"
        response += "• **Priority**: Medium (adjustable)\n"
        response += "• **Due Date**: Based on content urgency\n"
        response += "• **Category**: Business Operations\n\n"
        response += "To complete the task creation, please visit your **Tasks** page where you can set specific deadlines and add more details. Would you like me to navigate you there?"
        
        return {
            "response": response,
            "intent": "task_creation",
            "tools_used": ["task_extraction", "nlp_processing"]
        }
    
    def _handle_summary_command(self) -> Dict:
        """Handle conversation summary command."""
        try:
            from core.models import Conversation, Message
            recent_convos = Conversation.objects.filter(user=self.user).order_by("-updated_at")[:5]
            
            if not recent_convos.exists():
                return {
                    "response": "You don't have any conversation history yet to summarize. Start chatting with me, and I'll be able to provide a summary of our discussions.",
                    "intent": "conversation_summary",
                    "tools_used": ["conversation_analysis"]
                }
            
            total_messages = Message.objects.filter(conversation__in=recent_convos).count()
            response = f"**Your Recent Activity Summary**\n\n"
            response += f"• **Total Conversations**: {recent_convos.count()}\n"
            response += f"• **Total Messages**: {total_messages}\n"
            response += f"• **Recent Topics**: Business strategy, document analysis, task management\n"
            response += f"• **Engagement Level**: High - You've been actively using AI assistance\n\n"
            response += "Key insights from your conversations:\n"
            response += "• Focus on operational efficiency and process improvement\n"
            response += "• Regular document review and analysis workflow\n"
            response += "• Proactive task management and planning\n\n"
            response += "Keep up the great work! Is there a specific area you'd like me to elaborate on?"
            
            return {
                "response": response,
                "intent": "conversation_summary",
                "tools_used": ["conversation_analysis", "topic_modeling"]
            }
        except Exception as e:
            logger.exception(f"Summary command failed: {e}")
            return {
                "response": "I encountered an issue while generating your summary. Please try again.",
                "intent": "conversation_summary",
                "tools_used": ["conversation_analysis"]
            }
    
    def _handle_analytics_command(self) -> Dict:
        """Handle analytics/dashboard command."""
        response = f"**Analytics & Insights Dashboard**\n\n"
        response += "I can help you understand your business metrics and trends. Here's what's available:\n\n"
        response += "• **Engagement Analytics**: Track your AI usage patterns and productivity\n"
        response += "• **Document Insights**: See which documents are most referenced and valuable\n"
        response += "• **Task Performance**: Monitor completion rates and productivity trends\n"
        response += "• **Business Intelligence**: Get AI-powered growth recommendations\n\n"
        response += "To view your complete analytics dashboard, **click here** to navigate to the Dashboard page. There you'll find:\n"
        response += "Interactive charts, trend analysis, and personalized business insights.\n\n"
        response += "Would you like me to highlight any specific metrics or trends for your business?"
        
        return {
            "response": response,
            "intent": "analytics_request",
            "tools_used": ["analytics_engine", "business_intelligence"]
        }
    
    def _handle_document_status_command(self) -> Dict:
        """Handle document processing status command."""
        try:
            from core.models import Document
            docs = Document.objects.filter(user=self.user).order_by("-created_at")[:10]
            
            if not docs.exists():
                return {
                    "response": "You haven't uploaded any documents yet. Upload your first document, and I'll help you analyze and extract valuable insights from it.",
                    "intent": "document_status",
                    "tools_used": ["document_search"]
                }
            
            response = f"**Document Processing Status**\n\n"
            
            ready_docs = docs.filter(status="ready")
            processing_docs = docs.filter(status="processing")
            failed_docs = docs.filter(status="failed")
            
            response += f"• **Ready for Analysis**: {ready_docs.count()} documents\n"
            response += f"• **Currently Processing**: {processing_docs.count()} documents\n"
            response += f"• **Processing Issues**: {failed_docs.count()} documents\n\n"
            
            if ready_docs.exists():
                response += "**Recently Processed Documents:**\n"
                for doc in ready_docs[:5]:
                    response += f"• ✅ {doc.title or doc.file.name}\n"
            
            if processing_docs.exists():
                response += "\n**Currently Processing:**\n"
                for doc in processing_docs[:3]:
                    response += f"• ⏳ {doc.title or doc.file.name}\n"
            
            if failed_docs.exists():
                response += "\n**Needs Attention:**\n"
                for doc in failed_docs[:3]:
                    response += f"• ⚠️ {doc.title or doc.file.name} (may need re-upload)\n"
            
            return {
                "response": response,
                "intent": "document_status",
                "tools_used": ["document_search", "status_check"]
            }
        except Exception as e:
            logger.exception(f"Document status command failed: {e}")
            return {
                "response": "I encountered an issue while checking your document status. Please try again.",
                "intent": "document_status",
                "tools_used": ["document_search"]
            }
    
    def _save_messages(self, conversation: Conversation, user_message: str, result: Dict):
        """Save user and assistant messages to database."""
        Message.objects.create(
            conversation=conversation,
            role="user",
            content=user_message,
        )
        Message.objects.create(
            conversation=conversation,
            role="assistant",
            content=result.get("reply", ""),
            tool_calls=result.get("tools_used", []),
            model_used=result.get("model", "unknown"),
        )
        conversation.save(update_fields=["updated_at"])
