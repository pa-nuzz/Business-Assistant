import { MessageSquare, FileText, Kanban, Target, Lock, Zap } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Footer } from "@/components/landing/footer";

const features = [
  { icon: MessageSquare, title: "AI-Powered Chat", desc: "Context-aware conversations with multi-provider AI and real-time streaming." },
  { icon: FileText, title: "Document Intelligence", desc: "Upload PDFs, DOCX, TXT for instant analysis, summarization, and insight extraction." },
  { icon: Kanban, title: "Task Management", desc: "Visual Kanban board with drag-and-drop and AI-suggested tasks from conversations." },
  { icon: Target, title: "Goal Tracking", desc: "Set business goals and let AI track progress and surface blockers." },
  { icon: Lock, title: "Enterprise Security", desc: "JWT auth, httpOnly cookies, rate limiting, and audit logging." },
  { icon: Zap, title: "Real-Time Everything", desc: "WebSocket streaming, instant notifications, and live board updates." },
];

export default function FeaturesPage() {
  return (
    <div className="min-h-screen bg-background">
      <header className="border-b border-border">
        <div className="container mx-auto px-6 py-4 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
              <span className="text-primary-foreground font-bold text-sm">A</span>
            </div>
            <span className="font-semibold text-foreground">AEIOU AI</span>
          </Link>
          <nav className="hidden md:flex items-center gap-6 text-sm">
            <Link href="/features" className="text-foreground font-medium">Features</Link>
            <Link href="/pricing" className="text-muted-foreground hover:text-foreground">Pricing</Link>
            <Link href="/about" className="text-muted-foreground hover:text-foreground">About</Link>
            <Link href="/contact" className="text-muted-foreground hover:text-foreground">Contact</Link>
          </nav>
          <div className="flex items-center gap-3">
            <Link href="/login"><Button variant="ghost" size="sm">Sign In</Button></Link>
            <Link href="/register"><Button size="sm">Get Started</Button></Link>
          </div>
        </div>
      </header>

      <section className="py-20 md:py-28">
        <div className="container mx-auto px-6 text-center">
          <h1 className="text-4xl md:text-6xl font-bold tracking-tight text-foreground mb-6">
            Everything you need to <span className="text-primary">run your business</span>
          </h1>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto mb-12">
            One intelligent workspace replacing chat apps, document tools, and task boards.
          </p>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-5xl mx-auto text-left">
            {features.map((f, i) => {
              const Icon = f.icon;
              return (
                <div key={i} className="p-6 rounded-2xl bg-card border border-border hover:border-primary/30 transition-colors">
                  <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center mb-4">
                    <Icon className="w-5 h-5 text-primary" />
                  </div>
                  <h3 className="text-lg font-semibold text-foreground mb-2">{f.title}</h3>
                  <p className="text-sm text-muted-foreground leading-relaxed">{f.desc}</p>
                </div>
              );
            })}
          </div>

          <div className="mt-12">
            <Link href="/register">
              <Button size="lg" className="h-12 px-8">
                Start Free <Zap className="ml-2 w-4 h-4" />
              </Button>
            </Link>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
}
