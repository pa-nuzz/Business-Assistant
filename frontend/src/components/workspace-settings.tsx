"use client";

import { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { 
  Users, Settings, Shield, UserPlus, MoreHorizontal, 
  Trash2, Crown, UserCog, User as UserIcon, Eye,
  X, Check, ChevronDown
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { 
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger 
} from "@/components/ui/dialog";
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger
} from "@/components/ui/dropdown-menu";
import api from "@/lib/api";
import { toast } from "sonner";

interface Workspace {
  id: string;
  name: string;
  description: string;
  role: string;
  is_owner: boolean;
  member_count: number;
}

interface Member {
  id: string;
  user: {
    id: number;
    username: string;
    email: string;
    first_name: string;
    last_name: string;
  };
  role: 'owner' | 'admin' | 'member' | 'viewer';
  joined_at: string;
  invited_by?: string;
}

interface WorkspaceSettingsProps {
  workspaceId: string;
  isOpen: boolean;
  onClose: () => void;
}

const ROLE_ICONS = {
  owner: <Crown className="h-4 w-4 text-yellow-500" />,
  admin: <Shield className="h-4 w-4 text-blue-500" />,
  member: <UserIcon className="h-4 w-4 text-green-500" />,
  viewer: <Eye className="h-4 w-4 text-gray-500" />,
};

const ROLE_LABELS = {
  owner: 'Owner',
  admin: 'Admin',
  member: 'Member',
  viewer: 'Viewer',
};

const ROLE_PERMISSIONS = {
  owner: ['Full access', 'Manage members', 'Manage settings', 'Delete workspace'],
  admin: ['Create & edit', 'Manage members', 'View all'],
  member: ['Create & edit own', 'View all'],
  viewer: ['View only'],
};

export function WorkspaceSettings({ workspaceId, isOpen, onClose }: WorkspaceSettingsProps) {
  const [workspace, setWorkspace] = useState<Workspace | null>(null);
  const [members, setMembers] = useState<Member[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'members' | 'settings'>('members');
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState<'admin' | 'member' | 'viewer'>('member');
  const [isInviting, setIsInviting] = useState(false);

  const fetchWorkspace = useCallback(async () => {
    try {
      const response = await api.get(`/workspaces/${workspaceId}/`);
      setWorkspace(response.data);
    } catch (error) {
      toast.error('Failed to load workspace');
    }
  }, [workspaceId]);

  const fetchMembers = useCallback(async () => {
    try {
      const response = await api.get(`/workspaces/${workspaceId}/members/`);
      setMembers(response.data.members);
    } catch (error) {
      toast.error('Failed to load members');
    }
  }, [workspaceId]);

  useEffect(() => {
    if (isOpen) {
      setLoading(true);
      Promise.all([fetchWorkspace(), fetchMembers()]).finally(() => setLoading(false));
    }
  }, [isOpen, fetchWorkspace, fetchMembers]);

  const inviteMember = async () => {
    if (!inviteEmail.trim()) return;
    
    setIsInviting(true);
    try {
      await api.post(`/workspaces/${workspaceId}/members/invite/`, {
        email: inviteEmail,
        role: inviteRole,
      });
      toast.success('Invitation sent');
      setInviteEmail('');
      fetchMembers();
    } catch (error: any) {
      toast.error(error.response?.data?.error || 'Failed to invite member');
    } finally {
      setIsInviting(false);
    }
  };

  const updateRole = async (memberId: string, newRole: string) => {
    try {
      await api.patch(`/workspaces/${workspaceId}/members/${memberId}/role/`, {
        role: newRole,
      });
      toast.success('Role updated');
      fetchMembers();
    } catch (error: any) {
      toast.error(error.response?.data?.error || 'Failed to update role');
    }
  };

  const removeMember = async (memberId: string) => {
    try {
      await api.delete(`/workspaces/${workspaceId}/members/${memberId}/remove/`);
      toast.success('Member removed');
      fetchMembers();
    } catch (error: any) {
      toast.error(error.response?.data?.error || 'Failed to remove member');
    }
  };

  const canManageRole = (currentRole: string, targetRole: string) => {
    const hierarchy = { owner: 4, admin: 3, member: 2, viewer: 1 };
    return hierarchy[currentRole as keyof typeof hierarchy] > hierarchy[targetRole as keyof typeof hierarchy];
  };

  const currentUserRole = workspace?.role || 'viewer';
  const canInvite = ['owner', 'admin'].includes(currentUserRole);
  const canManageMembers = currentUserRole === 'owner' || currentUserRole === 'admin';

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-hidden">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Settings className="h-5 w-5" />
            Workspace Settings
          </DialogTitle>
        </DialogHeader>

        {/* Tabs */}
        <div className="flex gap-4 border-b mb-4">
          <button
            className={`pb-2 text-sm font-medium transition-colors ${
              activeTab === 'members'
                ? 'border-b-2 border-primary text-primary'
                : 'text-muted-foreground hover:text-foreground'
            }`}
            onClick={() => setActiveTab('members')}
          >
            <Users className="h-4 w-4 inline mr-2" />
            Members ({members.length})
          </button>
          {workspace?.is_owner && (
            <button
              className={`pb-2 text-sm font-medium transition-colors ${
                activeTab === 'settings'
                  ? 'border-b-2 border-primary text-primary'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
              onClick={() => setActiveTab('settings')}
            >
              <Settings className="h-4 w-4 inline mr-2" />
              General
            </button>
          )}
        </div>

        {loading ? (
          <div className="space-y-3">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="h-12 bg-muted rounded animate-pulse" />
            ))}
          </div>
        ) : activeTab === 'members' ? (
          <div className="space-y-4">
            {/* Invite Member */}
            {canInvite && (
              <div className="flex gap-2 p-3 bg-muted rounded-lg">
                <Input
                  placeholder="Enter email to invite..."
                  value={inviteEmail}
                  onChange={(e) => setInviteEmail(e.target.value)}
                  className="flex-1"
                />
                <select
                  value={inviteRole}
                  onChange={(e) => setInviteRole(e.target.value as any)}
                  className="px-3 py-2 rounded-md border text-sm"
                >
                  <option value="admin">Admin</option>
                  <option value="member">Member</option>
                  <option value="viewer">Viewer</option>
                </select>
                <Button 
                  onClick={inviteMember}
                  disabled={!inviteEmail.trim() || isInviting}
                  className="gap-2"
                >
                  <UserPlus className="h-4 w-4" />
                  Invite
                </Button>
              </div>
            )}

            {/* Members List */}
            <div className="space-y-2 max-h-[400px] overflow-y-auto">
              {members.map((member) => (
                <div
                  key={member.id}
                  className="flex items-center justify-between p-3 bg-muted/50 rounded-lg"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
                      {member.user.first_name[0]?.toUpperCase() || member.user.username[0].toUpperCase()}
                    </div>
                    <div>
                      <p className="font-medium">
                        {member.user.first_name} {member.user.last_name}
                        {member.user.first_name && (
                          <span className="text-muted-foreground font-normal ml-2">
                            @{member.user.username}
                          </span>
                        )}
                      </p>
                      <p className="text-sm text-muted-foreground">
                        {member.user.email}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    {/* Role Badge */}
                    {canManageMembers && canManageRole(currentUserRole, member.role) && member.role !== 'owner' ? (
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="outline" size="sm" className="gap-1">
                            {ROLE_ICONS[member.role]}
                            {ROLE_LABELS[member.role]}
                            <ChevronDown className="h-3 w-3" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          {['admin', 'member', 'viewer'].map((role) => (
                            <DropdownMenuItem
                              key={role}
                              onClick={() => updateRole(member.id, role)}
                              className="gap-2"
                            >
                              {ROLE_ICONS[role as keyof typeof ROLE_ICONS]}
                              {ROLE_LABELS[role as keyof typeof ROLE_LABELS]}
                              {member.role === role && <Check className="h-4 w-4 ml-auto" />}
                            </DropdownMenuItem>
                          ))}
                        </DropdownMenuContent>
                      </DropdownMenu>
                    ) : (
                      <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-muted text-sm">
                        {ROLE_ICONS[member.role]}
                        {ROLE_LABELS[member.role]}
                      </span>
                    )}

                    {/* Remove Button */}
                    {canManageMembers && 
                     canManageRole(currentUserRole, member.role) && 
                     member.role !== 'owner' && (
                      <Button
                        variant="ghost"
                        size="icon"
                        className="text-red-500 hover:text-red-600"
                        onClick={() => removeMember(member.id)}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    )}
                  </div>
                </div>
              ))}
            </div>

            {/* Role Legend */}
            <div className="mt-4 p-3 bg-muted rounded-lg text-sm">
              <p className="font-medium mb-2">Role Permissions</p>
              <div className="grid grid-cols-2 gap-2">
                {Object.entries(ROLE_PERMISSIONS).map(([role, perms]) => (
                  <div key={role} className="flex items-start gap-2">
                    {ROLE_ICONS[role as keyof typeof ROLE_ICONS]}
                    <div>
                      <span className="font-medium">{ROLE_LABELS[role as keyof typeof ROLE_LABELS]}:</span>
                      <span className="text-muted-foreground ml-1">
                        {perms.join(', ')}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            {/* General Settings */}
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium">Workspace Name</label>
                <Input 
                  defaultValue={workspace?.name} 
                  className="mt-1"
                  placeholder="Workspace name"
                />
              </div>
              <div>
                <label className="text-sm font-medium">Description</label>
                <Input 
                  defaultValue={workspace?.description}
                  className="mt-1"
                  placeholder="Description"
                />
              </div>
              <div className="flex items-center justify-between p-3 bg-muted rounded-lg">
                <div>
                  <p className="font-medium">Danger Zone</p>
                  <p className="text-sm text-muted-foreground">
                    Delete this workspace and all its data
                  </p>
                </div>
                <Button variant="destructive" size="sm">
                  <Trash2 className="h-4 w-4 mr-1" />
                  Delete
                </Button>
              </div>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
