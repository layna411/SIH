import React from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { UserRole } from '../types';
import { LoadingSpinner } from '../components/common/LoadingSpinner';

export const ProtectedRoute: React.FC<{ 
  allowedRoles?: UserRole[]; 
  allowBureauMembers?: boolean;
}> = ({ allowedRoles, allowBureauMembers = false }) => {
  const { user, isAuthenticated, isLoading, hasRole, isBureauMember } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <LoadingSpinner message="Verifying institutional session..." />
      </div>
    );
  }

  if (!isAuthenticated || !user) {
    return <Navigate to="/login" replace />;
  }

  const rolePermitted = allowedRoles ? hasRole(allowedRoles) : true;
  const bureauPermitted = allowBureauMembers && isBureauMember;

  if (!rolePermitted && !bureauPermitted) {
    // User does not possess the required role or bureau membership for this portal
    if (user.default_role === 'STUDENT') return <Navigate to="/student" replace />;
    if (user.default_role === 'COLLEGE_OFFICER') return <Navigate to="/officer" replace />;
    if (user.default_role === 'INSTITUTION_HEAD') return <Navigate to="/head" replace />;
    if (user.default_role === 'REGULATORY_ADMIN') return <Navigate to="/regulatory" replace />;
    if (user.default_role === 'SUPER_ADMIN') return <Navigate to="/admin" replace />;
    return <Navigate to="/" replace />;
  }

  return <Outlet />;
};
