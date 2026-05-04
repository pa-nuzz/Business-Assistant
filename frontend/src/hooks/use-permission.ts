"use client";

import { useState, useEffect, useCallback } from "react";
import api from "@/lib/api";

interface UsePermissionOptions {
  workspaceId?: string;
  resourceType?: string;
  resourceId?: string;
}

export function usePermission(options: UsePermissionOptions = {}) {
  const [role, setRole] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const checkWorkspacePermission = useCallback(async (
    permission: string
  ): Promise<boolean> => {
    if (!options.workspaceId) return false;
    
    try {
      const response = await api.get(
        `/workspaces/${options.workspaceId}/check-permission/?permission=${permission}`
      );
      return response.data.has_permission;
    } catch (err) {
      return false;
    }
  }, [options.workspaceId]);

  const checkResourcePermission = useCallback(async (
    action: string
  ): Promise<boolean> => {
    if (!options.resourceType || !options.resourceId) return false;
    
    try {
      const response = await api.post('/permissions/resource-check/', {
        resource_type: options.resourceType,
        resource_id: options.resourceId,
        action: action,
      });
      return response.data.can_manage;
    } catch (err) {
      return false;
    }
  }, [options.resourceType, options.resourceId]);

  useEffect(() => {
    const fetchRole = async () => {
      if (!options.workspaceId) {
        setLoading(false);
        return;
      }

      try {
        const response = await api.get(`/workspaces/${options.workspaceId}/`);
        setRole(response.data.my_role);
      } catch (err: any) {
        setError(err.response?.data?.error || 'Failed to check permissions');
      } finally {
        setLoading(false);
      }
    };

    fetchRole();
  }, [options.workspaceId]);

  // Role hierarchy
  const isOwner = role === 'owner';
  const isAdmin = role === 'admin' || isOwner;
  const isMember = role === 'member' || isAdmin;
  const isViewer = role === 'viewer' || isMember;

  return {
    role,
    loading,
    error,
    isOwner,
    isAdmin,
    isMember,
    isViewer,
    checkWorkspacePermission,
    checkResourcePermission,
  };
}

// Permission guard component
interface PermissionGuardProps {
  workspaceId?: string;
  permission: 'view' | 'edit' | 'delete' | 'manage' | 'owner';
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

export function PermissionGuard({ 
  workspaceId, 
  permission, 
  children, 
  fallback = null 
}: PermissionGuardProps) {
  const { isOwner, isAdmin, isMember, isViewer, loading } = usePermission({ workspaceId });

  if (loading) {
    return null;
  }

  const hasPermission = {
    view: isViewer,
    edit: isMember,
    delete: isAdmin,
    manage: isAdmin,
    owner: isOwner,
  }[permission];

  if (!hasPermission) {
    return fallback;
  }

  return children;
}
