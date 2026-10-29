import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { api } from '../../services/api';
import { 
  Institution, 
  GrievanceCategory, 
  User, 
  UserRole, 
  DashboardStats, 
  UserInvitation, 
  UserInviteResponse,
  InstitutionAlias,
  OrganizationalUnit,
  BureauMembership,
  OrgUnitType
} from '../../types';
import { LoadingSpinner } from '../../components/common/LoadingSpinner';
import { Modal } from '../../components/common/Modal';
import { 
  Activity, 
  Building2, 
  Users, 
  Layers, 
  Plus, 
  CheckCircle2, 
  ShieldCheck, 
  Search, 
  Edit2, 
  Zap, 
  Server, 
  AlertCircle,
  UserPlus,
  Mail,
  Copy,
  Check,
  RotateCcw,
  Ban,
  Filter,
  ExternalLink,
  ShieldAlert,
  Tag,
  Trash2,
  RefreshCw
} from 'lucide-react';

export const SuperAdminDashboard: React.FC = () => {
  const { user } = useAuth();
  const location = useLocation();

  const [activeTab, setActiveTab] = useState<'overview' | 'institutions' | 'users' | 'categories' | 'bureaus'>('overview');
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [institutions, setInstitutions] = useState<Institution[]>([]);
  const [categories, setCategories] = useState<GrievanceCategory[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [invitations, setInvitations] = useState<UserInvitation[]>([]);
  const [health, setHealth] = useState<{ status: string; app: string; environment: string; version: string } | null>(null);
  const [dbHealth, setDbHealth] = useState<{ status: string; database: string; driver: string; host: string; port: number; database_name: string } | null>(null);
  const [loading, setLoading] = useState(true);

  // Escalation engine state
  const [processingEscalations, setProcessingEscalations] = useState(false);
  const [escalationResult, setEscalationResult] = useState<string | null>(null);

  // New Institution Modal state
  const [isAddInstModalOpen, setIsAddInstModalOpen] = useState(false);
  const [instCode, setInstCode] = useState('');
  const [instName, setInstName] = useState('');
  const [instState, setInstState] = useState('');
  const [instCity, setInstCity] = useState('');
  const [instEmail, setInstEmail] = useState('');
  const [instAicteId, setInstAicteId] = useState('');
  const [instRegion, setInstRegion] = useState('');
  const [creatingInst, setCreatingInst] = useState(false);
  const [instSuccessModalOpen, setInstSuccessModalOpen] = useState(false);
  const [createdInstInfo, setCreatedInstInfo] = useState<{
    name: string;
    code: string;
    email: string;
    defaultPassword?: string;
  } | null>(null);
  const [copiedInstCreds, setCopiedInstCreds] = useState(false);

  // Phase B: AICTE Verification Modal state
  const [verifyingInst, setVerifyingInst] = useState<Institution | null>(null);
  const [aicteIdInput, setAicteIdInput] = useState('');
  const [aicteRegionInput, setAicteRegionInput] = useState('');
  const [submittingVerify, setSubmittingVerify] = useState(false);

  // Phase B: Institution Alias Modal state
  const [aliasInst, setAliasInst] = useState<Institution | null>(null);
  const [aliasesList, setAliasesList] = useState<InstitutionAlias[]>([]);
  const [newAliasName, setNewAliasName] = useState('');
  const [newAliasSource, setNewAliasSource] = useState('OFFICIAL_AISHE');
  const [loadingAliases, setLoadingAliases] = useState(false);
  const [submittingAlias, setSubmittingAlias] = useState(false);

  // Phase B: Organizational Units State
  const [orgUnits, setOrgUnits] = useState<OrganizationalUnit[]>([]);
  const [seedingUnits, setSeedingUnits] = useState(false);
  const [isUnitModalOpen, setIsUnitModalOpen] = useState(false);
  const [editingUnit, setEditingUnit] = useState<OrganizationalUnit | null>(null);
  const [unitCode, setUnitCode] = useState('');
  const [unitName, setUnitName] = useState('');
  const [unitType, setUnitType] = useState<OrgUnitType>('BUREAU');
  const [unitRegionCode, setUnitRegionCode] = useState('');
  const [unitParentId, setUnitParentId] = useState<string>('');
  const [unitDesc, setUnitDesc] = useState('');
  const [savingUnit, setSavingUnit] = useState(false);

  // Phase B: Bureau Memberships Modal State
  const [selectedUnitForMembers, setSelectedUnitForMembers] = useState<OrganizationalUnit | null>(null);
  const [unitMembers, setUnitMembers] = useState<BureauMembership[]>([]);
  const [loadingMembers, setLoadingMembers] = useState(false);
  const [assignUserId, setAssignUserId] = useState<string>('');
  const [assignRole, setAssignRole] = useState('BUREAU_OFFICER');
  const [assignDesignation, setAssignDesignation] = useState('');
  const [assigningMember, setAssigningMember] = useState(false);

  // Category SLA edit state
  const [editingCategory, setEditingCategory] = useState<GrievanceCategory | null>(null);
  const [newSlaDays, setNewSlaDays] = useState(7);
  const [savingCategory, setSavingCategory] = useState(false);

  // User Management State
  const [userSubTab, setUserSubTab] = useState<'active' | 'invitations'>('active');
  const [userSearch, setUserSearch] = useState('');
  const [filterRole, setFilterRole] = useState<string>('ALL');
  const [filterInstitution, setFilterInstitution] = useState<string>('ALL');
  const [filterStatus, setFilterStatus] = useState<string>('ALL');

  // Add User / Invite Modal state
  const [isAddUserModalOpen, setIsAddUserModalOpen] = useState(false);
  const [inviteFullName, setInviteFullName] = useState('');
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState<UserRole>('COLLEGE_OFFICER');
  const [inviteInstId, setInviteInstId] = useState<string>('');
  const [inviteDept, setInviteDept] = useState('Academic Affairs');
  const [inviteDesignation, setInviteDesignation] = useState('');
  const [inviteStaffId, setInviteStaffId] = useState('');
  const [inviteState, setInviteState] = useState('Delhi');
  const [inviteCode, setInviteCode] = useState('');
  const [invitingUser, setInvitingUser] = useState(false);
  const [inviteError, setInviteError] = useState<string | null>(null);

  // Invitation Success Modal
  const [inviteSuccessModalOpen, setInviteSuccessModalOpen] = useState(false);
  const [createdInvite, setCreatedInvite] = useState<UserInviteResponse | null>(null);
  const [copiedLink, setCopiedLink] = useState(false);

  // Sync activeTab from route
  useEffect(() => {
    if (location.pathname.includes('/admin/users')) {
      setActiveTab('users');
    } else if (location.pathname.includes('/admin/institutions')) {
      setActiveTab('institutions');
    } else if (location.pathname.includes('/admin/categories')) {
      setActiveTab('categories');
    } else if (location.pathname.includes('/admin/bureaus')) {
      setActiveTab('bureaus');
    } else {
      setActiveTab('overview');
    }
  }, [location.pathname]);

  const fetchAllData = async () => {
    try {
      setLoading(true);
      const [statsData, instData, catData, userData, healthRes, dbHealthRes, invData, orgUnitsRes] = await Promise.allSettled([
        api.get<DashboardStats>('/analytics/dashboard'),
        api.get<Institution[]>('/institutions'),
        api.get<GrievanceCategory[]>('/categories'),
        api.get<User[]>('/users'),
        api.get<{ status: string; app: string; environment: string; version: string }>('/health'),
        api.get<{ status: string; database: string; driver: string; host: string; port: number; database_name: string }>('/health/db'),
        api.get<UserInvitation[]>('/users/invitations/list'),
        api.get<OrganizationalUnit[]>('/organizational-units')
      ]);

      if (statsData.status === 'fulfilled') setStats(statsData.value);
      if (instData.status === 'fulfilled') {
        setInstitutions(instData.value);
        if (instData.value.length > 0 && !inviteInstId) {
          setInviteInstId(String(instData.value[0].id));
        }
      }
      if (catData.status === 'fulfilled') setCategories(catData.value);
      if (userData.status === 'fulfilled') setUsers(userData.value);
      if (healthRes.status === 'fulfilled') setHealth(healthRes.value);
      if (dbHealthRes.status === 'fulfilled') setDbHealth(dbHealthRes.value);
      if (invData.status === 'fulfilled') setInvitations(invData.value);
      if (orgUnitsRes.status === 'fulfilled') setOrgUnits(orgUnitsRes.value);
    } catch (err) {
      console.error('Failed to load SuperAdmin dashboard data', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAllData();
  }, []);

  const handleProcessEscalations = async () => {
    if (!window.confirm('Run national batch overdue escalation engine? Grievances exceeding statutory SLA thresholds across all institutions will be automatically escalated.')) {
      return;
    }
    setProcessingEscalations(true);
    setEscalationResult(null);
    try {
      const res = await api.post<{ escalated_count: number; escalated_reference_numbers: string[] }>('/grievances/escalations/process-overdue');
      if (res.escalated_count > 0) {
        setEscalationResult(`Successfully escalated ${res.escalated_count} overdue grievance(s): ${res.escalated_reference_numbers.join(', ')}`);
      } else {
        setEscalationResult('All grievances platform-wide are currently compliant within SLA deadlines.');
      }
      await fetchAllData();
    } catch (err: any) {
      alert(err.message || 'Failed to process overdue escalations.');
    } finally {
      setProcessingEscalations(false);
    }
  };

  const handleCreateInstitution = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreatingInst(true);
    try {
      const created = await api.post<Institution>('/institutions', {
        institution_code: instCode.trim().toUpperCase(),
        code: instCode.trim().toUpperCase(),
        name: instName.trim(),
        state: instState.trim(),
        city: instCity.trim(),
        official_email: instEmail.trim().toLowerCase(),
        contact_email: instEmail.trim().toLowerCase(),
        aicte_permanent_id: instAicteId.trim() || undefined,
        region: instRegion.trim() || undefined,
      });
      setInstitutions((prev) => [...prev, created]);
      setIsAddInstModalOpen(false);
      setCreatedInstInfo({
        name: created.name,
        code: created.code || created.institution_code || instCode.trim().toUpperCase(),
        email: created.admin_account_email || created.official_email || instEmail.trim().toLowerCase(),
        defaultPassword: created.default_password || 'EduResolve@123',
      });
      setInstSuccessModalOpen(true);
      setInstCode('');
      setInstName('');
      setInstState('');
      setInstCity('');
      setInstEmail('');
      setInstAicteId('');
      setInstRegion('');
      await fetchAllData();
    } catch (err: any) {
      alert(err.message || 'Failed to create institution.');
    } finally {
      setCreatingInst(false);
    }
  };

  // Phase B: AICTE Verification Handler
  const openVerifyModal = (inst: Institution) => {
    setVerifyingInst(inst);
    setAicteIdInput(inst.aicte_permanent_id || '');
    setAicteRegionInput(inst.region || '');
  };

  const handleVerifyAICTE = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!verifyingInst) return;
    setSubmittingVerify(true);
    try {
      const updated = await api.post<Institution>(`/institutions/${verifyingInst.id}/verify-aicte`, {
        aicte_permanent_id: aicteIdInput.trim() || undefined,
        region: aicteRegionInput.trim() || undefined,
        is_aicte_verified: true,
        verification_notes: 'Verified by Super Administrator via Management Console'
      });
      setInstitutions((prev) => prev.map((inst) => (inst.id === updated.id ? updated : inst)));
      setVerifyingInst(null);
    } catch (err: any) {
      alert(err.message || 'Failed to verify institution.');
    } finally {
      setSubmittingVerify(false);
    }
  };

  // Phase B: Aliases Handlers
  const openAliasModal = async (inst: Institution) => {
    setAliasInst(inst);
    setLoadingAliases(true);
    setNewAliasName('');
    setNewAliasSource('OFFICIAL_AISHE');
    try {
      const res = await api.get<InstitutionAlias[]>(`/institutions/${inst.id}/aliases`);
      setAliasesList(res);
    } catch (err: any) {
      console.error('Failed to load aliases', err);
      setAliasesList([]);
    } finally {
      setLoadingAliases(false);
    }
  };

  const handleAddAlias = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!aliasInst || !newAliasName.trim()) return;
    setSubmittingAlias(true);
    try {
      const added = await api.post<InstitutionAlias>(`/institutions/${aliasInst.id}/aliases`, {
        alias_name: newAliasName.trim(),
        source: newAliasSource.trim() || 'ADMIN_ENTRY',
        is_verified: true
      });
      setAliasesList((prev) => [...prev, added]);
      setNewAliasName('');
      const updatedInsts = await api.get<Institution[]>('/institutions');
      setInstitutions(updatedInsts);
    } catch (err: any) {
      alert(err.message || 'Failed to add alias.');
    } finally {
      setSubmittingAlias(false);
    }
  };

  const handleDeleteAlias = async (aliasId: number) => {
    if (!aliasInst) return;
    if (!window.confirm('Are you sure you want to remove this alias?')) return;
    try {
      await api.delete(`/institutions/${aliasInst.id}/aliases/${aliasId}`);
      setAliasesList((prev) => prev.filter((a) => a.id !== aliasId));
      const updatedInsts = await api.get<Institution[]>('/institutions');
      setInstitutions(updatedInsts);
    } catch (err: any) {
      alert(err.message || 'Failed to delete alias.');
    }
  };

  // Phase B: Organizational Units Handlers
  const handleSeedUnits = async () => {
    if (!window.confirm('Seed standard AICTE baseline units (RB, PGRC, AB, RO_NORTH, RO_WEST, RO_SOUTH)? Existing records will be preserved safely.')) return;
    setSeedingUnits(true);
    try {
      const res = await api.post<{ seeded_count: number; message: string }>('/organizational-units/seed-defaults');
      alert(res.message);
      const units = await api.get<OrganizationalUnit[]>('/organizational-units');
      setOrgUnits(units);
    } catch (err: any) {
      alert(err.message || 'Failed to seed units.');
    } finally {
      setSeedingUnits(false);
    }
  };

  const openAddUnitModal = () => {
    setEditingUnit(null);
    setUnitCode('');
    setUnitName('');
    setUnitType('BUREAU');
    setUnitRegionCode('');
    setUnitParentId('');
    setUnitDesc('');
    setIsUnitModalOpen(true);
  };

  const openEditUnitModal = (unit: OrganizationalUnit) => {
    setEditingUnit(unit);
    setUnitCode(unit.code);
    setUnitName(unit.name);
    setUnitType(unit.unit_type);
    setUnitRegionCode(unit.region_code || '');
    setUnitParentId(unit.parent_unit_id ? String(unit.parent_unit_id) : '');
    setUnitDesc(unit.description || '');
    setIsUnitModalOpen(true);
  };

  const handleSaveUnit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSavingUnit(true);
    try {
      if (editingUnit) {
        const updated = await api.put<OrganizationalUnit>(`/organizational-units/${editingUnit.id}`, {
          name: unitName.trim(),
          unit_type: unitType,
          description: unitDesc.trim() || undefined,
          parent_unit_id: unitParentId ? Number(unitParentId) : null,
          region_code: unitRegionCode.trim() || undefined
        });
        setOrgUnits((prev) => prev.map((u) => (u.id === updated.id ? updated : u)));
      } else {
        const created = await api.post<OrganizationalUnit>('/organizational-units', {
          code: unitCode.trim().toUpperCase(),
          name: unitName.trim(),
          unit_type: unitType,
          description: unitDesc.trim() || undefined,
          parent_unit_id: unitParentId ? Number(unitParentId) : undefined,
          region_code: unitRegionCode.trim() || undefined
        });
        setOrgUnits((prev) => [...prev, created]);
      }
      setIsUnitModalOpen(false);
      setEditingUnit(null);
    } catch (err: any) {
      alert(err.message || 'Failed to save organizational unit.');
    } finally {
      setSavingUnit(false);
    }
  };

  const handleToggleUnitActive = async (targetUnit: OrganizationalUnit) => {
    const newActive = !targetUnit.is_active;
    const action = newActive ? 'activate' : 'deactivate';
    if (!window.confirm(`Are you sure you want to ${action} ${targetUnit.code} (${targetUnit.name})?`)) return;
    try {
      const updated = await api.put<OrganizationalUnit>(`/organizational-units/${targetUnit.id}`, {
        is_active: newActive
      });
      setOrgUnits((prev) => prev.map((u) => (u.id === updated.id ? updated : u)));
    } catch (err: any) {
      alert(err.message || `Failed to ${action} organizational unit.`);
    }
  };

  // Phase B: Bureau Membership Handlers
  const openMembersModal = async (unit: OrganizationalUnit) => {
    setSelectedUnitForMembers(unit);
    setLoadingMembers(true);
    setAssignUserId('');
    setAssignRole('BUREAU_OFFICER');
    setAssignDesignation('');
    try {
      const members = await api.get<BureauMembership[]>(`/organizational-units/${unit.id}/members`);
      setUnitMembers(members);
    } catch (err: any) {
      console.error('Failed to load members', err);
      setUnitMembers([]);
    } finally {
      setLoadingMembers(false);
    }
  };

  const handleAssignMember = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedUnitForMembers || !assignUserId) return;
    setAssigningMember(true);
    try {
      const assigned = await api.post<BureauMembership>(`/organizational-units/${selectedUnitForMembers.id}/members`, {
        user_id: Number(assignUserId),
        membership_role: assignRole,
        designation: assignDesignation.trim() || undefined
      });
      setUnitMembers((prev) => [...prev, assigned]);
      setAssignUserId('');
      setAssignDesignation('');
      const updatedUnits = await api.get<OrganizationalUnit[]>('/organizational-units');
      setOrgUnits(updatedUnits);
    } catch (err: any) {
      alert(err.message || 'Failed to assign member to Bureau.');
    } finally {
      setAssigningMember(false);
    }
  };

  const handleRevokeMember = async (memId: number) => {
    if (!selectedUnitForMembers) return;
    if (!window.confirm('Are you sure you want to revoke this user from the Bureau?')) return;
    try {
      await api.delete(`/organizational-units/${selectedUnitForMembers.id}/members/${memId}`);
      setUnitMembers((prev) => prev.filter((m) => m.id !== memId));
      const updatedUnits = await api.get<OrganizationalUnit[]>('/organizational-units');
      setOrgUnits(updatedUnits);
    } catch (err: any) {
      alert(err.message || 'Failed to revoke bureau membership.');
    }
  };

  const handleUpdateCategorySLA = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingCategory) return;
    setSavingCategory(true);
    try {
      const updated = await api.put<GrievanceCategory>(`/categories/${editingCategory.id}`, {
        default_sla_days: Number(newSlaDays),
      });
      setCategories((prev) => prev.map((c) => (c.id === updated.id ? updated : c)));
      setEditingCategory(null);
    } catch (err: any) {
      alert(err.message || 'Failed to update category SLA.');
    } finally {
      setSavingCategory(false);
    }
  };

  const handleRoleChange = async (targetUserId: number, newRole: UserRole) => {
    try {
      const updated = await api.put<User>(`/users/${targetUserId}/role`, { role: newRole });
      setUsers((prev) => prev.map((u) => (u.id === targetUserId ? updated : u)));
    } catch (err: any) {
      alert(err.message || 'Failed to update user role.');
    }
  };

  const handleToggleUserStatus = async (targetUser: User) => {
    const newStatus = !targetUser.is_active;
    const actionText = newStatus ? 'activate' : 'deactivate';
    if (!window.confirm(`Are you sure you want to ${actionText} the account for ${targetUser.full_name}?`)) {
      return;
    }
    try {
      const updated = await api.put<User>(`/users/${targetUser.id}/status`, { is_active: newStatus });
      setUsers((prev) => prev.map((u) => (u.id === targetUser.id ? updated : u)));
    } catch (err: any) {
      alert(err.message || `Failed to ${actionText} account.`);
    }
  };

  const handleInviteUser = async (e: React.FormEvent) => {
    e.preventDefault();
    setInviteError(null);
    setInvitingUser(true);

    try {
      const payload: any = {
        email: inviteEmail.trim().toLowerCase(),
        full_name: inviteFullName.trim(),
        role: inviteRole,
        staff_id_number: inviteStaffId.trim() || undefined,
        designation: inviteDesignation.trim() || undefined,
      };

      if (inviteRole === 'COLLEGE_OFFICER' || inviteRole === 'INSTITUTION_HEAD') {
        if (!inviteInstId) {
          throw new Error('Please select an institution for this officer/head.');
        }
        payload.institution_id = Number(inviteInstId);
        if (inviteRole === 'COLLEGE_OFFICER') {
          payload.department = inviteDept;
        }
      } else if (inviteRole === 'REGULATORY_ADMIN') {
        if (!inviteState) {
          throw new Error('Please specify the state jurisdiction for the regulatory admin.');
        }
        payload.jurisdiction_state = inviteState.trim();
        payload.jurisdiction_code = inviteCode.trim() || `JUR-${inviteState.toUpperCase().substring(0, 3)}-01`;
      }

      const res = await api.post<UserInviteResponse>('/users/invite', payload);
      setCreatedInvite(res);
      setIsAddUserModalOpen(false);
      setInviteSuccessModalOpen(true);

      // Reset form
      setInviteFullName('');
      setInviteEmail('');
      setInviteDesignation('');
      setInviteStaffId('');
      setInviteCode('');

      // Refresh users and invitations
      const [uRes, invRes] = await Promise.all([
        api.get<User[]>('/users'),
        api.get<UserInvitation[]>('/users/invitations/list')
      ]);
      setUsers(uRes);
      setInvitations(invRes);
    } catch (err: any) {
      setInviteError(err.message || 'Failed to send invitation. Please verify all fields.');
    } finally {
      setInvitingUser(false);
    }
  };

  const handleRevokeInvitation = async (id: number) => {
    if (!window.confirm('Are you sure you want to revoke this invitation? The link will be immediately invalidated.')) {
      return;
    }
    try {
      await api.delete(`/users/invitations/${id}`);
      setInvitations((prev) => prev.map((inv) => (inv.id === id ? { ...inv, status: 'REVOKED' } : inv)));
    } catch (err: any) {
      alert(err.message || 'Failed to revoke invitation.');
    }
  };

  const handleResendInvitation = async (id: number) => {
    try {
      const res = await api.post<UserInviteResponse>(`/users/invitations/${id}/resend`);
      setCreatedInvite(res);
      setInviteSuccessModalOpen(true);
      const invRes = await api.get<UserInvitation[]>('/users/invitations/list');
      setInvitations(invRes);
    } catch (err: any) {
      alert(err.message || 'Failed to resend invitation.');
    }
  };

  const handleCopyLink = () => {
    if (createdInvite?.invitation_link) {
      navigator.clipboard.writeText(createdInvite.invitation_link);
      setCopiedLink(true);
      setTimeout(() => setCopiedLink(false), 2500);
    }
  };

  // Filtered Users
  const filteredUsers = users.filter((u) => {
    // Search
    if (userSearch.trim()) {
      const q = userSearch.toLowerCase();
      const matchName = u.full_name?.toLowerCase().includes(q);
      const matchEmail = u.email?.toLowerCase().includes(q);
      const matchId = u.student_id_number?.toLowerCase().includes(q);
      if (!matchName && !matchEmail && !matchId) return false;
    }
    // Role
    if (filterRole !== 'ALL' && u.default_role !== filterRole) {
      return false;
    }
    // Institution
    if (filterInstitution !== 'ALL') {
      const targetInstId = Number(filterInstitution);
      const hasInst = u.memberships?.some((m) => m.institution_id === targetInstId);
      if (!hasInst) return false;
    }
    // Status
    if (filterStatus === 'ACTIVE' && !u.is_active) return false;
    if (filterStatus === 'INACTIVE' && u.is_active) return false;

    return true;
  });

  if (loading) {
    return <LoadingSpinner message="Loading platform configuration and registry..." />;
  }

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <span className="text-xs font-bold text-purple-600 bg-purple-50 px-2.5 py-1 rounded-md border border-purple-200 uppercase tracking-wide">
            Platform Master Administration
          </span>
          <h1 className="text-xl sm:text-2xl font-bold text-slate-900 mt-2">
            System Administration & Governance
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Role-based account management, institution directory, AI model telemetry, and nationwide SLA enforcement.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={handleProcessEscalations}
            disabled={processingEscalations}
            className="inline-flex items-center gap-2 px-3.5 py-2.5 rounded-xl bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 font-semibold text-xs transition shadow-sm disabled:opacity-50"
            title="Scan for statutory SLA deadline breaches across all institutions and auto-escalate"
          >
            <Zap className={`w-4 h-4 ${processingEscalations ? 'animate-spin' : 'text-rose-600'}`} />
            {processingEscalations ? 'Processing SLA Checks...' : 'Run National Escalation Engine'}
          </button>

          <button
            onClick={() => setIsAddInstModalOpen(true)}
            className="inline-flex items-center gap-1.5 px-3.5 py-2.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-xs transition shadow-sm"
          >
            <Building2 className="w-4 h-4" />
            Register Institution
          </button>

          <button
            onClick={() => {
              setInviteError(null);
              setIsAddUserModalOpen(true);
            }}
            className="inline-flex items-center gap-1.5 px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs transition shadow-sm"
          >
            <UserPlus className="w-4 h-4" />
            Add User
          </button>
        </div>
      </div>

      {escalationResult && (
        <div className="p-4 rounded-xl bg-indigo-50 border border-indigo-200 text-indigo-900 text-xs flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-indigo-600 flex-shrink-0" />
            <span>{escalationResult}</span>
          </div>
          <button 
            onClick={() => setEscalationResult(null)}
            className="text-indigo-500 hover:text-indigo-800 font-bold ml-4"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Tabs Bar */}
      <div className="flex items-center gap-6 border-b border-slate-200 text-xs font-semibold overflow-x-auto">
        <button
          onClick={() => setActiveTab('overview')}
          className={`pb-3 transition flex items-center gap-1.5 whitespace-nowrap ${
            activeTab === 'overview'
              ? 'border-b-2 border-blue-600 text-blue-600'
              : 'text-slate-500 hover:text-slate-800'
          }`}
        >
          <Activity className="w-4 h-4" /> System Overview
        </button>
        <button
          onClick={() => setActiveTab('users')}
          className={`pb-3 transition flex items-center gap-1.5 whitespace-nowrap ${
            activeTab === 'users'
              ? 'border-b-2 border-blue-600 text-blue-600'
              : 'text-slate-500 hover:text-slate-800'
          }`}
        >
          <Users className="w-4 h-4" /> User Management ({users.length})
        </button>
        <button
          onClick={() => setActiveTab('institutions')}
          className={`pb-3 transition flex items-center gap-1.5 whitespace-nowrap ${
            activeTab === 'institutions'
              ? 'border-b-2 border-blue-600 text-blue-600'
              : 'text-slate-500 hover:text-slate-800'
          }`}
        >
          <Building2 className="w-4 h-4" /> Institutions ({institutions.length})
        </button>
        <button
          onClick={() => setActiveTab('categories')}
          className={`pb-3 transition flex items-center gap-1.5 whitespace-nowrap ${
            activeTab === 'categories'
              ? 'border-b-2 border-blue-600 text-blue-600'
              : 'text-slate-500 hover:text-slate-800'
          }`}
        >
          <Layers className="w-4 h-4" /> Categories & SLA ({categories.length})
        </button>
        <button
          onClick={() => setActiveTab('bureaus')}
          className={`pb-3 transition flex items-center gap-1.5 whitespace-nowrap ${
            activeTab === 'bureaus'
              ? 'border-b-2 border-blue-600 text-blue-600'
              : 'text-slate-500 hover:text-slate-800'
          }`}
        >
          <ShieldCheck className="w-4 h-4" /> AICTE Bureaus & Units ({orgUnits.length})
        </button>
      </div>

      {/* Tab 1: System Health & AI Overview */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1">Total Grievances</span>
              <p className="text-2xl font-extrabold text-slate-900">{stats?.total_grievances || 0}</p>
              <span className="text-[11px] text-slate-400">Platform-wide filings</span>
            </div>
            <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1">Registered Users</span>
              <p className="text-2xl font-extrabold text-blue-600">{users.length}</p>
              <span className="text-[11px] text-slate-400">Authorized accounts</span>
            </div>
            <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1">Active Colleges</span>
              <p className="text-2xl font-extrabold text-indigo-600">{institutions.length}</p>
              <span className="text-[11px] text-slate-400">Verified entities</span>
            </div>
            <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1">Avg Resolution</span>
              <p className="text-2xl font-extrabold text-emerald-600">{stats?.avg_resolution_days || 0}d</p>
              <span className="text-[11px] text-slate-400">National SLA standard</span>
            </div>
          </div>

          {/* Live Infrastructure Health */}
          <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm">
            <h3 className="text-sm font-bold text-slate-900 mb-3 flex items-center gap-2">
              <Server className="w-4 h-4 text-emerald-600" />
              Live Infrastructure Health & Database Connection
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
              <div className="p-4 rounded-xl bg-slate-50 border border-slate-100 flex items-start gap-3">
                <div className={`p-2 rounded-lg ${health?.status === 'healthy' ? 'bg-emerald-100 text-emerald-700' : 'bg-rose-100 text-rose-700'}`}>
                  <Server className="w-5 h-5" />
                </div>
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-slate-900">FastAPI Core Service</span>
                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                      health?.status === 'healthy' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-rose-50 text-rose-700'
                    }`}>
                      {health?.status ? health.status.toUpperCase() : 'UNKNOWN'}
                    </span>
                  </div>
                  <p className="text-slate-500 text-[11px]">Environment: {health?.environment || 'development'}</p>
                  <p className="text-slate-400 text-[10px]">Endpoint: /api/v1/health</p>
                </div>
              </div>

              <div className="p-4 rounded-xl bg-slate-50 border border-slate-100 flex items-start gap-3">
                <div className={`p-2 rounded-lg ${dbHealth?.database === 'healthy' ? 'bg-emerald-100 text-emerald-700' : 'bg-rose-100 text-rose-700'}`}>
                  <CheckCircle2 className="w-5 h-5" />
                </div>
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-slate-900">XAMPP MySQL Database</span>
                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                      dbHealth?.database === 'healthy' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-rose-50 text-rose-700'
                    }`}>
                      {dbHealth?.database ? dbHealth.database.toUpperCase() : 'UNKNOWN'}
                    </span>
                  </div>
                  <p className="text-slate-500 text-[11px]">Engine: MariaDB/MySQL ({dbHealth?.driver || 'mysql+pymysql'})</p>
                  <p className="text-slate-400 text-[10px]">Schema: {dbHealth?.database_name || 'eduresolve_ai'} on {dbHealth?.host}:{dbHealth?.port}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: User Management (Section 2 & 3) */}
      {activeTab === 'users' && (
        <div className="space-y-4">
          {/* Sub-navigation & Add User Header */}
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 bg-white p-4 rounded-2xl border border-slate-200/80 shadow-sm">
            <div className="flex items-center gap-2">
              <button
                onClick={() => setUserSubTab('active')}
                className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition ${
                  userSubTab === 'active'
                    ? 'bg-blue-600 text-white shadow-xs'
                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                }`}
              >
                Registered Accounts ({filteredUsers.length})
              </button>
              <button
                onClick={() => setUserSubTab('invitations')}
                className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition ${
                  userSubTab === 'invitations'
                    ? 'bg-blue-600 text-white shadow-xs'
                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                }`}
              >
                Pending Invitations ({invitations.filter((i) => i.status === 'PENDING').length})
              </button>
            </div>

            <button
              onClick={() => {
                setInviteError(null);
                setIsAddUserModalOpen(true);
              }}
              className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs transition shadow-sm"
            >
              <UserPlus className="w-4 h-4" />
              Invite Privileged User
            </button>
          </div>

          {userSubTab === 'active' && (
            <div className="bg-white rounded-2xl border border-slate-200/80 shadow-sm overflow-hidden space-y-4">
              {/* Search & Filter Toolbar */}
              <div className="p-4 border-b border-slate-100 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-xs">
                {/* Search */}
                <div className="relative">
                  <input
                    type="text"
                    placeholder="Search name, email, roll/staff ID..."
                    value={userSearch}
                    onChange={(e) => setUserSearch(e.target.value)}
                    className="w-full pl-9 pr-3 py-2 rounded-xl border border-slate-200 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  />
                  <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                </div>

                {/* Filter by Role */}
                <div>
                  <select
                    value={filterRole}
                    onChange={(e) => setFilterRole(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-slate-200 bg-white focus:outline-none focus:ring-1 focus:ring-blue-500 text-slate-700"
                  >
                    <option value="ALL">All Roles (Any)</option>
                    <option value="COLLEGE_OFFICER">College Officer</option>
                    <option value="INSTITUTION_HEAD">Institution Head</option>
                    <option value="REGULATORY_ADMIN">Regulatory Admin</option>
                    <option value="SUPER_ADMIN">Super Admin</option>
                    <option value="STUDENT">Student</option>
                  </select>
                </div>

                {/* Filter by Institution */}
                <div>
                  <select
                    value={filterInstitution}
                    onChange={(e) => setFilterInstitution(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-slate-200 bg-white focus:outline-none focus:ring-1 focus:ring-blue-500 text-slate-700"
                  >
                    <option value="ALL">All Institutions</option>
                    {institutions.map((inst) => (
                      <option key={inst.id} value={inst.id}>
                        {inst.name} ({inst.code})
                      </option>
                    ))}
                  </select>
                </div>

                {/* Filter by Status */}
                <div>
                  <select
                    value={filterStatus}
                    onChange={(e) => setFilterStatus(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-slate-200 bg-white focus:outline-none focus:ring-1 focus:ring-blue-500 text-slate-700"
                  >
                    <option value="ALL">All Account Statuses</option>
                    <option value="ACTIVE">Active Only</option>
                    <option value="INACTIVE">Deactivated Only</option>
                  </select>
                </div>
              </div>

              {/* Users Table */}
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-50 text-slate-500 uppercase tracking-wider">
                    <tr>
                      <th className="py-3 px-4">User</th>
                      <th className="py-3 px-4">Email</th>
                      <th className="py-3 px-4">Role</th>
                      <th className="py-3 px-4">Affiliation / Jurisdiction</th>
                      <th className="py-3 px-4">Status</th>
                      <th className="py-3 px-4 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 text-slate-700">
                    {filteredUsers.length === 0 ? (
                      <tr>
                        <td colSpan={6} className="py-8 text-center text-slate-400">
                          No user accounts match the selected criteria.
                        </td>
                      </tr>
                    ) : (
                      filteredUsers.map((u) => {
                        const instAffiliation = u.memberships?.[0]?.institution_name;
                        const jurAffiliation = u.regulatory_jurisdictions?.[0]
                          ? `${u.regulatory_jurisdictions[0].state} (${u.regulatory_jurisdictions[0].jurisdiction_code})`
                          : null;
                        const displayAffiliation = instAffiliation || jurAffiliation || (u.default_role === 'SUPER_ADMIN' ? 'Platform Wide' : 'Independent');

                        return (
                          <tr key={u.id} className="hover:bg-slate-50 transition">
                            <td className="py-3 px-4">
                              <div className="flex items-center gap-2.5">
                                <div className="w-7 h-7 rounded-lg bg-blue-600 text-white font-bold flex items-center justify-center text-[11px]">
                                  {u.full_name?.charAt(0).toUpperCase()}
                                </div>
                                <div>
                                  <span className="font-semibold text-slate-800 block">{u.full_name}</span>
                                  {u.student_id_number && (
                                    <span className="text-[10px] text-slate-400">ID: {u.student_id_number}</span>
                                  )}
                                </div>
                              </div>
                            </td>
                            <td className="py-3 px-4 text-slate-600 font-mono text-[11px]">{u.email}</td>
                            <td className="py-3 px-4">
                              <span className={`inline-block px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${
                                u.default_role === 'SUPER_ADMIN' ? 'bg-purple-100 text-purple-700 border border-purple-200' :
                                u.default_role === 'INSTITUTION_HEAD' ? 'bg-indigo-100 text-indigo-700 border border-indigo-200' :
                                u.default_role === 'COLLEGE_OFFICER' ? 'bg-blue-100 text-blue-700 border border-blue-200' :
                                u.default_role === 'REGULATORY_ADMIN' ? 'bg-amber-100 text-amber-700 border border-amber-200' :
                                'bg-slate-100 text-slate-600'
                              }`}>
                                {u.default_role.replace(/_/g, ' ')}
                              </span>
                            </td>
                            <td className="py-3 px-4 text-slate-600 max-w-xs truncate" title={displayAffiliation}>
                              {displayAffiliation}
                            </td>
                            <td className="py-3 px-4">
                              <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold ${
                                u.is_active
                                  ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                                  : 'bg-slate-100 text-slate-500 border border-slate-200'
                              }`}>
                                {u.is_active ? 'Active' : 'Deactivated'}
                              </span>
                            </td>
                            <td className="py-3 px-4 text-right">
                              <div className="inline-flex items-center gap-2">
                                {/* Role Switcher */}
                                <select
                                  value={u.default_role}
                                  onChange={(e) => handleRoleChange(u.id, e.target.value as UserRole)}
                                  disabled={u.id === user?.id}
                                  className="px-2 py-1 rounded-lg border border-slate-200 text-[11px] bg-white focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:opacity-40"
                                >
                                  <option value="STUDENT">STUDENT</option>
                                  <option value="COLLEGE_OFFICER">COLLEGE_OFFICER</option>
                                  <option value="INSTITUTION_HEAD">INSTITUTION_HEAD</option>
                                  <option value="REGULATORY_ADMIN">REGULATORY_ADMIN</option>
                                  <option value="SUPER_ADMIN">SUPER_ADMIN</option>
                                </select>

                                {/* Deactivate / Activate Button */}
                                {u.id !== user?.id && (
                                  <button
                                    onClick={() => handleToggleUserStatus(u)}
                                    className={`px-2 py-1 rounded-lg text-[11px] font-semibold transition border ${
                                      u.is_active
                                        ? 'bg-rose-50 text-rose-700 hover:bg-rose-100 border-rose-200'
                                        : 'bg-emerald-50 text-emerald-700 hover:bg-emerald-100 border-emerald-200'
                                    }`}
                                    title={u.is_active ? 'Deactivate user' : 'Reactivate user'}
                                  >
                                    {u.is_active ? 'Deactivate' : 'Activate'}
                                  </button>
                                )}
                              </div>
                            </td>
                          </tr>
                        );
                      })
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {userSubTab === 'invitations' && (
            <div className="bg-white rounded-2xl border border-slate-200/80 shadow-sm overflow-hidden">
              <div className="p-4 border-b border-slate-100 flex items-center justify-between">
                <div>
                  <h3 className="font-bold text-slate-900 text-xs">Issued Single-Use Invitations</h3>
                  <p className="text-[11px] text-slate-400 mt-0.5">
                    Invited administrators set their own password securely via expiring single-use links.
                  </p>
                </div>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-50 text-slate-500 uppercase tracking-wider">
                    <tr>
                      <th className="py-3 px-4">Invitee</th>
                      <th className="py-3 px-4">Email</th>
                      <th className="py-3 px-4">Assigned Role</th>
                      <th className="py-3 px-4">Institution / Scope</th>
                      <th className="py-3 px-4">Status</th>
                      <th className="py-3 px-4">Expires</th>
                      <th className="py-3 px-4 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 text-slate-700">
                    {invitations.length === 0 ? (
                      <tr>
                        <td colSpan={7} className="py-8 text-center text-slate-400">
                          No pending or historical invitations found.
                        </td>
                      </tr>
                    ) : (
                      invitations.map((inv) => (
                        <tr key={inv.id} className="hover:bg-slate-50 transition">
                          <td className="py-3 px-4 font-semibold text-slate-800">{inv.full_name}</td>
                          <td className="py-3 px-4 font-mono text-slate-600 text-[11px]">{inv.email}</td>
                          <td className="py-3 px-4">
                            <span className="font-mono text-[10px] font-bold px-2 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200">
                              {inv.role.replace(/_/g, ' ')}
                            </span>
                          </td>
                          <td className="py-3 px-4 text-slate-600">
                            {inv.institution_name || inv.jurisdiction_state || '—'}
                          </td>
                          <td className="py-3 px-4">
                            <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold ${
                              inv.status === 'ACCEPTED' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' :
                              inv.status === 'PENDING' ? 'bg-amber-50 text-amber-700 border border-amber-200' :
                              inv.status === 'EXPIRED' ? 'bg-slate-100 text-slate-500 border border-slate-200' :
                              'bg-rose-50 text-rose-700 border border-rose-200'
                            }`}>
                              {inv.status}
                            </span>
                          </td>
                          <td className="py-3 px-4 text-[11px] text-slate-500">
                            {new Date(inv.expires_at).toLocaleDateString()}
                          </td>
                          <td className="py-3 px-4 text-right">
                            <div className="inline-flex items-center gap-2">
                              {inv.status === 'PENDING' && (
                                <button
                                  onClick={() => handleRevokeInvitation(inv.id)}
                                  className="px-2 py-1 rounded-lg text-[10px] font-semibold bg-rose-50 text-rose-700 hover:bg-rose-100 border border-rose-200"
                                >
                                  Revoke
                                </button>
                              )}
                              {inv.status !== 'ACCEPTED' && (
                                <button
                                  onClick={() => handleResendInvitation(inv.id)}
                                  className="px-2 py-1 rounded-lg text-[10px] font-semibold bg-blue-50 text-blue-700 hover:bg-blue-100 border border-blue-200 flex items-center gap-1"
                                >
                                  <RotateCcw className="w-3 h-3" /> Resend
                                </button>
                              )}
                            </div>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Tab 3: Institutions Directory */}
      {activeTab === 'institutions' && (
        <div className="bg-white rounded-2xl border border-slate-200/80 shadow-sm overflow-hidden">
          <div className="p-4 border-b border-slate-100 flex flex-wrap items-center justify-between gap-2">
            <div>
              <h3 className="font-bold text-slate-900 text-xs">Registered Higher Education Institutions</h3>
              <p className="text-[11px] text-slate-500">AICTE Permanent IDs, Regional Affiliations, and Institutional Name Aliases</p>
            </div>
            <span className="text-[11px] font-semibold text-blue-700 bg-blue-50 px-2.5 py-1 rounded-lg border border-blue-200">
              {institutions.filter((i) => i.is_aicte_verified).length} / {institutions.length} AICTE Verified
            </span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-500 uppercase tracking-wider">
                <tr>
                  <th className="py-3 px-4">Code & AICTE ID</th>
                  <th className="py-3 px-4">Institution Name & Aliases</th>
                  <th className="py-3 px-4">Location & Region</th>
                  <th className="py-3 px-4">Official Contact</th>
                  <th className="py-3 px-4">AICTE Verification</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                {institutions.map((inst) => (
                  <tr key={inst.id} className="hover:bg-slate-50">
                    <td className="py-3 px-4 font-mono font-bold text-slate-900">
                      <div>{inst.code}</div>
                      {inst.aicte_permanent_id ? (
                        <span className="inline-block font-mono text-[10px] text-blue-700 bg-blue-50 px-1.5 py-0.5 rounded border border-blue-200 mt-1 font-semibold">
                          ID: {inst.aicte_permanent_id}
                        </span>
                      ) : (
                        <span className="inline-block text-[10px] text-amber-600 font-medium italic mt-1">
                          No AICTE ID
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-4">
                      <div className="font-semibold text-slate-800">{inst.name}</div>
                      {inst.alias_names && inst.alias_names.length > 0 && (
                        <div className="flex flex-wrap gap-1 mt-1">
                          {inst.alias_names.map((a) => (
                            <span key={a} className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded bg-slate-100 text-slate-600 text-[10px] font-medium border border-slate-200">
                              <Tag className="w-2.5 h-2.5 text-slate-400" />
                              {a}
                            </span>
                          ))}
                        </div>
                      )}
                    </td>
                    <td className="py-3 px-4">
                      <div>{inst.city}, {inst.state}</div>
                      {inst.region && (
                        <span className="inline-block text-[10px] text-indigo-700 font-semibold bg-indigo-50 px-1.5 py-0.5 rounded mt-0.5 border border-indigo-100">
                          {inst.region} Region
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-slate-600">{inst.contact_email}</td>
                    <td className="py-3 px-4">
                      {inst.is_aicte_verified ? (
                        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                          <CheckCircle2 className="w-3 h-3 text-emerald-600" /> AICTE Verified
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-amber-50 text-amber-700 border border-amber-200">
                          <AlertCircle className="w-3 h-3 text-amber-500" /> Pending
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <div className="inline-flex items-center gap-1.5">
                        <button
                          onClick={() => openAliasModal(inst)}
                          className="px-2 py-1 rounded-lg text-[11px] font-semibold bg-slate-100 hover:bg-blue-50 text-slate-700 hover:text-blue-700 border border-slate-200 transition flex items-center gap-1"
                          title="Manage Institutional Aliases"
                        >
                          <Tag className="w-3 h-3 text-slate-500" /> Aliases
                        </button>
                        <button
                          onClick={() => openVerifyModal(inst)}
                          className={`px-2 py-1 rounded-lg text-[11px] font-semibold border transition flex items-center gap-1 ${
                            inst.is_aicte_verified
                              ? 'bg-slate-50 hover:bg-slate-100 text-slate-700 border-slate-200'
                              : 'bg-emerald-50 hover:bg-emerald-100 text-emerald-700 border-emerald-200'
                          }`}
                          title="Verify or update official AICTE identifier"
                        >
                          <ShieldCheck className="w-3 h-3" />
                          {inst.is_aicte_verified ? 'Edit ID' : 'Verify'}
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 4: Categories & SLA */}
      {activeTab === 'categories' && (
        <div className="bg-white rounded-2xl border border-slate-200/80 shadow-sm overflow-hidden">
          <div className="p-4 border-b border-slate-100">
            <h3 className="font-bold text-slate-900 text-xs">Configured Grievance Categories & SLA Windows</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-500 uppercase tracking-wider">
                <tr>
                  <th className="py-3 px-4">Code</th>
                  <th className="py-3 px-4">Category Name</th>
                  <th className="py-3 px-4">Default SLA Window</th>
                  <th className="py-3 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                {categories.map((c) => (
                  <tr key={c.id} className="hover:bg-slate-50">
                    <td className="py-3 px-4 font-mono font-bold text-blue-600">{c.code}</td>
                    <td className="py-3 px-4 font-semibold text-slate-800">{c.name}</td>
                    <td className="py-3 px-4">{c.default_sla_days} Days Target</td>
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={() => {
                          setEditingCategory(c);
                          setNewSlaDays(c.default_sla_days);
                        }}
                        className="p-1 text-slate-500 hover:text-blue-600 rounded-lg hover:bg-slate-100"
                        title="Edit SLA"
                      >
                        <Edit2 className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 5: AICTE Organizational Units & Bureau Memberships */}
      {activeTab === 'bureaus' && (
        <div className="bg-white rounded-2xl border border-slate-200/80 shadow-sm overflow-hidden">
          <div className="p-4 border-b border-slate-100 flex flex-wrap items-center justify-between gap-3">
            <div>
              <h3 className="font-bold text-slate-900 text-xs">AICTE Organizational Units & Bureau Hierarchy</h3>
              <p className="text-[11px] text-slate-500">
                Statutory Bureaus, Grievance Cells, and Regional Offices managing cross-bureau oversight
              </p>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={handleSeedUnits}
                disabled={seedingUnits}
                className="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl bg-indigo-50 hover:bg-indigo-100 text-indigo-700 border border-indigo-200 font-semibold text-xs shadow-sm transition disabled:opacity-50"
                title="Idempotently seed standard baseline AICTE units: RB, PGRC, AB, RO_NORTH, RO_WEST, RO_SOUTH"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${seedingUnits ? 'animate-spin text-indigo-600' : ''}`} />
                {seedingUnits ? 'Seeding...' : 'Seed Baseline Units'}
              </button>
              <button
                onClick={openAddUnitModal}
                className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs shadow-sm transition"
              >
                <Plus className="w-3.5 h-3.5" />
                Add Organizational Unit
              </button>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-500 uppercase tracking-wider">
                <tr>
                  <th className="py-3 px-4">Code & Type</th>
                  <th className="py-3 px-4">Unit Name & Description</th>
                  <th className="py-3 px-4">Region / Hierarchy</th>
                  <th className="py-3 px-4">Assigned Personnel</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                {orgUnits.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="py-8 text-center text-slate-400">
                      No organizational units found. Click <strong>Seed Baseline Units</strong> to load initial AICTE structure.
                    </td>
                  </tr>
                ) : (
                  orgUnits.map((u) => (
                    <tr key={u.id} className="hover:bg-slate-50">
                      <td className="py-3 px-4">
                        <div className="font-mono font-bold text-slate-900">{u.code}</div>
                        <span className={`inline-block px-1.5 py-0.5 rounded text-[10px] font-bold border mt-0.5 ${
                          u.unit_type === 'BUREAU'
                            ? 'bg-purple-50 text-purple-700 border-purple-200'
                            : u.unit_type === 'CELL'
                            ? 'bg-amber-50 text-amber-700 border-amber-200'
                            : u.unit_type === 'REGIONAL_OFFICE'
                            ? 'bg-blue-50 text-blue-700 border-blue-200'
                            : 'bg-slate-100 text-slate-700 border-slate-200'
                        }`}>
                          {u.unit_type.replace('_', ' ')}
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        <div className="font-semibold text-slate-900">{u.name}</div>
                        {u.description && (
                          <div className="text-[11px] text-slate-500 line-clamp-1 mt-0.5">{u.description}</div>
                        )}
                      </td>
                      <td className="py-3 px-4">
                        <div className="text-slate-800 font-medium">
                          {u.region_code ? `${u.region_code} Region` : 'National Jurisdiction'}
                        </div>
                        {u.parent_code && (
                          <div className="text-[10px] text-slate-400 mt-0.5">
                            Parent: <span className="font-mono font-semibold text-slate-600">{u.parent_code}</span>
                          </div>
                        )}
                      </td>
                      <td className="py-3 px-4">
                        <span className="inline-flex items-center gap-1 font-semibold text-slate-800 bg-slate-100 px-2 py-0.5 rounded-full text-[11px]">
                          <Users className="w-3 h-3 text-slate-500" />
                          {u.active_members_count || 0} active
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold ${
                          u.is_active
                            ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                            : 'bg-rose-50 text-rose-700 border border-rose-200'
                        }`}>
                          {u.is_active ? 'ACTIVE' : 'INACTIVE'}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right">
                        <div className="inline-flex items-center gap-1.5">
                          <button
                            onClick={() => openMembersModal(u)}
                            className="px-2.5 py-1 rounded-lg text-[11px] font-semibold bg-blue-50 hover:bg-blue-100 text-blue-700 border border-blue-200 flex items-center gap-1 transition"
                            title="Manage personnel assigned to this bureau"
                          >
                            <Users className="w-3 h-3" /> Staff
                          </button>
                          <button
                            onClick={() => openEditUnitModal(u)}
                            className="p-1.5 text-slate-500 hover:text-blue-600 rounded-lg hover:bg-slate-100"
                            title="Edit Unit Properties"
                          >
                            <Edit2 className="w-3.5 h-3.5" />
                          </button>
                          <button
                            onClick={() => handleToggleUnitActive(u)}
                            className={`px-2 py-1 rounded-lg text-[10px] font-semibold border transition ${
                              u.is_active
                                ? 'bg-rose-50 text-rose-700 hover:bg-rose-100 border-rose-200'
                                : 'bg-emerald-50 text-emerald-700 hover:bg-emerald-100 border-emerald-200'
                            }`}
                          >
                            {u.is_active ? 'Deactivate' : 'Activate'}
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Add User / Invitation Modal (Section 3) */}
      <Modal
        isOpen={isAddUserModalOpen}
        onClose={() => setIsAddUserModalOpen(false)}
        title="Invite New Privileged Administrator"
        maxWidth="md"
      >
        <form onSubmit={handleInviteUser} className="space-y-4 text-xs">
          {inviteError && (
            <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0 text-rose-600" />
              <span>{inviteError}</span>
            </div>
          )}

          <div>
            <label className="block font-semibold text-slate-700 mb-1">Account Role *</label>
            <select
              value={inviteRole}
              onChange={(e) => setInviteRole(e.target.value as UserRole)}
              className="w-full px-3 py-2 rounded-xl border border-slate-300 font-semibold text-slate-800"
            >
              <option value="COLLEGE_OFFICER">College Officer (Intake & Redressal)</option>
              <option value="INSTITUTION_HEAD">Institution Head (Director / Vice Chancellor)</option>
              <option value="REGULATORY_ADMIN">Regulatory Admin (State Ombudsman)</option>
            </select>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block font-semibold text-slate-700 mb-1">Full Name *</label>
              <input
                type="text"
                required
                placeholder="e.g. Dr. Ramesh Kumar"
                value={inviteFullName}
                onChange={(e) => setInviteFullName(e.target.value)}
                className="w-full px-3 py-2 rounded-xl border border-slate-300"
              />
            </div>
            <div>
              <label className="block font-semibold text-slate-700 mb-1">Official Email *</label>
              <input
                type="email"
                required
                placeholder="officer@college.edu"
                value={inviteEmail}
                onChange={(e) => setInviteEmail(e.target.value)}
                className="w-full px-3 py-2 rounded-xl border border-slate-300"
              />
            </div>
          </div>

          {/* Conditional: Institution Selector for Officer & Head */}
          {(inviteRole === 'COLLEGE_OFFICER' || inviteRole === 'INSTITUTION_HEAD') && (
            <div>
              <label className="block font-semibold text-slate-700 mb-1">Institution Affiliation *</label>
              <select
                required
                value={inviteInstId}
                onChange={(e) => setInviteInstId(e.target.value)}
                className="w-full px-3 py-2 rounded-xl border border-slate-300 text-slate-800"
              >
                {institutions.map((inst) => (
                  <option key={inst.id} value={inst.id}>
                    {inst.name} ({inst.code}) — {inst.city}, {inst.state}
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Conditional: Department for Officer */}
          {inviteRole === 'COLLEGE_OFFICER' && (
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Assigned Department *</label>
                <select
                  value={inviteDept}
                  onChange={(e) => setInviteDept(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-slate-300 text-slate-800"
                >
                  <option value="Academic Affairs">Academic Affairs & Teaching</option>
                  <option value="Examination Cell">Examination Cell & Evaluation</option>
                  <option value="Hostel & Mess">Hostel & Accommodation</option>
                  <option value="Finance & Accounts">Finance & Student Accounts</option>
                  <option value="Anti-Ragging Cell">Anti-Ragging & Disciplinary</option>
                  <option value="Student Welfare">Student Welfare & Mentorship</option>
                  <option value="Administration">General Administration</option>
                  <option value="Infrastructure">Campus Infrastructure & IT</option>
                </select>
              </div>
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Designation</label>
                <input
                  type="text"
                  placeholder="e.g. Assistant Controller"
                  value={inviteDesignation}
                  onChange={(e) => setInviteDesignation(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-slate-300"
                />
              </div>
            </div>
          )}

          {/* Conditional: Jurisdiction for Regulatory Admin */}
          {inviteRole === 'REGULATORY_ADMIN' && (
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">State Jurisdiction *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Maharashtra"
                  value={inviteState}
                  onChange={(e) => setInviteState(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-slate-300"
                />
              </div>
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Jurisdiction Code</label>
                <input
                  type="text"
                  placeholder="e.g. REG-MH-01"
                  value={inviteCode}
                  onChange={(e) => setInviteCode(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-slate-300 font-mono uppercase"
                />
              </div>
            </div>
          )}

          <div className="pt-3 border-t border-slate-100 flex items-center justify-between">
            <span className="text-[11px] text-slate-400">
              User will set their own password via a single-use expiring token.
            </span>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => setIsAddUserModalOpen(false)}
                className="px-3.5 py-2 rounded-xl border border-slate-200 text-slate-600 font-semibold"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={invitingUser}
                className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold flex items-center gap-1.5 disabled:opacity-50"
              >
                {invitingUser ? 'Generating Invite...' : 'Generate & Send Invite'}
              </button>
            </div>
          </div>
        </form>
      </Modal>

      {/* Invitation Success Modal */}
      <Modal
        isOpen={inviteSuccessModalOpen}
        onClose={() => setInviteSuccessModalOpen(false)}
        title="Account Invitation Successfully Generated"
        maxWidth="md"
      >
        <div className="space-y-4 text-xs">
          <div className="p-4 rounded-2xl bg-emerald-50 border border-emerald-200 text-emerald-900 flex items-start gap-3">
            <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
            <div>
              <p className="font-bold text-sm">Invitation Created for {createdInvite?.full_name}</p>
              <p className="text-[11px] text-emerald-700 mt-0.5">
                Role: <span className="font-semibold uppercase">{createdInvite?.role.replace(/_/g, ' ')}</span> • Email: {createdInvite?.email}
              </p>
            </div>
          </div>

          <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 space-y-2">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 block">
              Single-Use Onboarding Link (Valid for 7 Days)
            </span>
            <div className="flex items-center gap-2">
              <input
                type="text"
                readOnly
                value={createdInvite?.invitation_link || ''}
                className="w-full px-3 py-2 rounded-xl border border-slate-300 font-mono text-[11px] bg-white text-slate-700"
              />
              <button
                onClick={handleCopyLink}
                className="px-3 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold flex items-center gap-1.5 shrink-0"
              >
                {copiedLink ? <Check className="w-4 h-4 text-emerald-300" /> : <Copy className="w-4 h-4" />}
                {copiedLink ? 'Copied!' : 'Copy'}
              </button>
            </div>
          </div>

          <div className="p-3.5 rounded-xl bg-amber-50 border border-amber-200 text-amber-900 text-[11px] leading-relaxed">
            <span className="font-bold block mb-0.5">Development Environment Advisory:</span>
            SMTP mailer is not currently configured. Share the secure invitation link directly with the user so they can set their password and activate their account.
          </div>

          <div className="flex justify-end pt-2">
            <button
              onClick={() => setInviteSuccessModalOpen(false)}
              className="px-4 py-2 rounded-xl bg-slate-900 text-white font-semibold"
            >
              Done
            </button>
          </div>
        </div>
      </Modal>

      {/* Add Institution Modal */}
      <Modal
        isOpen={isAddInstModalOpen}
        onClose={() => setIsAddInstModalOpen(false)}
        title="Register New Higher Education Institution"
        maxWidth="md"
      >
        <form onSubmit={handleCreateInstitution} className="space-y-4 text-xs">
          <div>
            <label className="block font-semibold text-slate-700 mb-1">Institution Code *</label>
            <input
              type="text"
              required
              placeholder="e.g. IITD01"
              value={instCode}
              onChange={(e) => setInstCode(e.target.value)}
              className="w-full px-3 py-2 rounded-xl border border-slate-300 font-mono uppercase"
            />
          </div>
          <div>
            <label className="block font-semibold text-slate-700 mb-1">Full Institution Name *</label>
            <input
              type="text"
              required
              placeholder="e.g. Indian Institute of Technology Delhi"
              value={instName}
              onChange={(e) => setInstName(e.target.value)}
              className="w-full px-3 py-2 rounded-xl border border-slate-300"
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block font-semibold text-slate-700 mb-1">State *</label>
              <input
                type="text"
                required
                placeholder="e.g. Delhi"
                value={instState}
                onChange={(e) => setInstState(e.target.value)}
                className="w-full px-3 py-2 rounded-xl border border-slate-300"
              />
            </div>
            <div>
              <label className="block font-semibold text-slate-700 mb-1">City *</label>
              <input
                type="text"
                required
                placeholder="e.g. New Delhi"
                value={instCity}
                onChange={(e) => setInstCity(e.target.value)}
                className="w-full px-3 py-2 rounded-xl border border-slate-300"
              />
            </div>
          </div>
          <div>
            <label className="block font-semibold text-slate-700 mb-1">Grievance Cell Contact Email *</label>
            <input
              type="email"
              required
              placeholder="grievance@iitd.ac.in"
              value={instEmail}
              onChange={(e) => setInstEmail(e.target.value)}
              className="w-full px-3 py-2 rounded-xl border border-slate-300"
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block font-semibold text-slate-700 mb-1">AICTE Permanent ID (Optional)</label>
              <input
                type="text"
                placeholder="e.g. 1-123456789"
                value={instAicteId}
                onChange={(e) => setInstAicteId(e.target.value)}
                className="w-full px-3 py-2 rounded-xl border border-slate-300 font-mono"
              />
            </div>
            <div>
              <label className="block font-semibold text-slate-700 mb-1">AICTE Region (Optional)</label>
              <select
                value={instRegion}
                onChange={(e) => setInstRegion(e.target.value)}
                className="w-full px-3 py-2 rounded-xl border border-slate-300 text-slate-800"
              >
                <option value="">Select Region...</option>
                <option value="Northern">Northern</option>
                <option value="North-Western">North-Western</option>
                <option value="Western">Western</option>
                <option value="Central">Central</option>
                <option value="Eastern">Eastern</option>
                <option value="Southern">Southern</option>
                <option value="South-Western">South-Western</option>
              </select>
            </div>
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={() => setIsAddInstModalOpen(false)}
              className="px-4 py-2 rounded-xl border border-slate-200 text-slate-600 font-semibold"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={creatingInst}
              className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold disabled:opacity-50"
            >
              {creatingInst ? 'Registering...' : 'Register Institution'}
            </button>
          </div>
        </form>
      </Modal>

      {/* Institution Registration Success Modal */}
      <Modal
        isOpen={instSuccessModalOpen}
        onClose={() => setInstSuccessModalOpen(false)}
        title="Institution Successfully Registered"
        maxWidth="md"
      >
        <div className="space-y-4 text-xs">
          <div className="p-4 rounded-2xl bg-emerald-50 border border-emerald-200 text-emerald-900 flex items-start gap-3">
            <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
            <div>
              <p className="font-bold text-sm">{createdInstInfo?.name}</p>
              <p className="text-[11px] text-emerald-700 mt-0.5">
                Code: <span className="font-mono font-semibold uppercase">{createdInstInfo?.code}</span> • Status: <span className="font-semibold text-emerald-800">VERIFIED</span>
              </p>
            </div>
          </div>

          <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 space-y-3">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 block">
              Default Administrator Login Credentials
            </span>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div className="p-3 rounded-xl bg-white border border-slate-200">
                <span className="text-[10px] text-slate-400 font-semibold block uppercase">Login Email</span>
                <span className="font-mono text-slate-800 font-semibold select-all text-xs">{createdInstInfo?.email}</span>
              </div>
              <div className="p-3 rounded-xl bg-white border border-slate-200">
                <span className="text-[10px] text-slate-400 font-semibold block uppercase">Default Password</span>
                <span className="font-mono text-blue-700 font-bold select-all text-xs">{createdInstInfo?.defaultPassword}</span>
              </div>
            </div>

            <div className="flex justify-end pt-1">
              <button
                type="button"
                onClick={() => {
                  const creds = `Institution: ${createdInstInfo?.name} (${createdInstInfo?.code})\nLogin Email: ${createdInstInfo?.email}\nDefault Password: ${createdInstInfo?.defaultPassword}\nLogin URL: ${window.location.origin}/login`;
                  navigator.clipboard.writeText(creds);
                  setCopiedInstCreds(true);
                  setTimeout(() => setCopiedInstCreds(false), 2500);
                }}
                className="px-3 py-1.5 rounded-lg bg-blue-50 hover:bg-blue-100 text-blue-700 font-semibold flex items-center gap-1.5 transition text-[11px]"
              >
                {copiedInstCreds ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5 text-blue-600" />}
                {copiedInstCreds ? 'Credentials Copied!' : 'Copy Credentials'}
              </button>
            </div>
          </div>

          <div className="p-3.5 rounded-xl bg-blue-50 border border-blue-200 text-blue-900 text-[11px] leading-relaxed">
            <span className="font-bold block mb-0.5">Password Change Notice:</span>
            An <strong>Institution Head</strong> account has been configured with this default password. After logging in with this account, the institution administrator can change their password anytime via <strong>Profile Settings</strong>.
          </div>

          <div className="flex justify-end pt-2">
            <button
              onClick={() => setInstSuccessModalOpen(false)}
              className="px-4 py-2 rounded-xl bg-slate-900 text-white font-semibold"
            >
              Done
            </button>
          </div>
        </div>
      </Modal>

      {/* Configure SLA Modal */}
      {editingCategory && (
        <Modal
          isOpen={true}
          onClose={() => setEditingCategory(null)}
          title={`Configure SLA: ${editingCategory.name}`}
          maxWidth="sm"
        >
          <form onSubmit={handleUpdateCategorySLA} className="space-y-4 text-xs">
            <div>
              <label className="block font-semibold text-slate-700 mb-1">SLA Target Resolution (Days) *</label>
              <input
                type="number"
                min={1}
                max={90}
                required
                value={newSlaDays}
                onChange={(e) => setNewSlaDays(Number(e.target.value))}
                className="w-full px-3 py-2 rounded-xl border border-slate-300"
              />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setEditingCategory(null)}
                className="px-4 py-2 rounded-xl border border-slate-200 text-slate-600"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={savingCategory}
                className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold"
              >
                {savingCategory ? 'Saving...' : 'Save SLA'}
              </button>
            </div>
          </form>
        </Modal>
      )}

      {/* Phase B: Verify AICTE Permanent ID Modal */}
      {verifyingInst && (
        <Modal
          isOpen={true}
          onClose={() => setVerifyingInst(null)}
          title={`Verify AICTE Permanent ID: ${verifyingInst.name}`}
          maxWidth="md"
        >
          <form onSubmit={handleVerifyAICTE} className="space-y-4 text-xs">
            <div className="p-3.5 rounded-xl bg-blue-50 border border-blue-200 text-blue-900 leading-relaxed">
              <span className="font-bold block mb-1">Statutory Verification Notice:</span>
              Confirming or modifying an official AICTE Permanent ID grants verified status in the EduResolve AI cross-bureau registry. All verification actions are immutably logged to the administrative audit trail.
            </div>

            <div>
              <label className="block font-semibold text-slate-700 mb-1">AICTE Permanent Registration ID *</label>
              <input
                type="text"
                required
                placeholder="e.g. 1-123456789"
                value={aicteIdInput}
                onChange={(e) => setAicteIdInput(e.target.value)}
                className="w-full px-3 py-2 rounded-xl border border-slate-300 font-mono text-sm uppercase"
              />
            </div>

            <div>
              <label className="block font-semibold text-slate-700 mb-1">AICTE Region *</label>
              <select
                required
                value={aicteRegionInput}
                onChange={(e) => setAicteRegionInput(e.target.value)}
                className="w-full px-3 py-2 rounded-xl border border-slate-300 text-slate-800"
              >
                <option value="">Select Region...</option>
                <option value="Northern">Northern</option>
                <option value="North-Western">North-Western</option>
                <option value="Western">Western</option>
                <option value="Central">Central</option>
                <option value="Eastern">Eastern</option>
                <option value="Southern">Southern</option>
                <option value="South-Western">South-Western</option>
              </select>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setVerifyingInst(null)}
                className="px-4 py-2 rounded-xl border border-slate-200 text-slate-600 font-semibold"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={submittingVerify}
                className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-semibold flex items-center gap-1.5 disabled:opacity-50"
              >
                <CheckCircle2 className="w-3.5 h-3.5" />
                {submittingVerify ? 'Verifying...' : 'Confirm AICTE Verification'}
              </button>
            </div>
          </form>
        </Modal>
      )}

      {/* Phase B: Institution Aliases Management Modal */}
      {aliasInst && (
        <Modal
          isOpen={true}
          onClose={() => setAliasInst(null)}
          title={`Institution Name Aliases: ${aliasInst.name}`}
          maxWidth="lg"
        >
          <div className="space-y-4 text-xs">
            <p className="text-slate-500">
              Manage alternative institution names, common acronyms, and historical names. Aliases empower grievance search and AI-assisted cross-bureau matching without merging separate institution records.
            </p>

            {/* Existing Aliases Roster */}
            <div className="bg-slate-50 rounded-xl border border-slate-200 overflow-hidden">
              <div className="p-3 border-b border-slate-200 flex items-center justify-between">
                <span className="font-bold text-slate-700 uppercase tracking-wider text-[10px]">
                  Registered Aliases ({aliasesList.length})
                </span>
                {loadingAliases && <span className="text-[10px] text-blue-600 animate-pulse font-semibold">Loading...</span>}
              </div>
              <div className="max-h-52 overflow-y-auto divide-y divide-slate-100">
                {aliasesList.length === 0 ? (
                  <div className="p-4 text-center text-slate-400">No aliases configured for this institution.</div>
                ) : (
                  aliasesList.map((a) => (
                    <div key={a.id} className="p-3 flex items-center justify-between hover:bg-white transition">
                      <div className="space-y-0.5">
                        <div className="font-semibold text-slate-900 flex items-center gap-2">
                          <Tag className="w-3 h-3 text-blue-600" />
                          <span>{a.alias_name}</span>
                          <span className="font-mono text-[10px] text-slate-400">({a.normalized_alias})</span>
                        </div>
                        <div className="text-[10px] text-slate-500">
                          Source: <span className="font-semibold text-slate-700">{a.source || 'ADMIN_ENTRY'}</span>
                        </div>
                      </div>
                      <button
                        onClick={() => handleDeleteAlias(a.id)}
                        className="p-1.5 text-rose-500 hover:text-rose-700 hover:bg-rose-50 rounded-lg transition"
                        title="Remove alias"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Add New Alias Form */}
            <form onSubmit={handleAddAlias} className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-3">
              <span className="font-bold text-slate-800 block text-xs">Add New Name Alias / Acronym</span>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Alias Name *</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. IITD or IIT Delhi"
                    value={newAliasName}
                    onChange={(e) => setNewAliasName(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-slate-300"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Provenance / Source</label>
                  <select
                    value={newAliasSource}
                    onChange={(e) => setNewAliasSource(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-slate-300 text-slate-800"
                  >
                    <option value="OFFICIAL_AISHE">AISHE / AICTE Database</option>
                    <option value="COMMONLY_KNOWN_AS">Commonly Known As / Short Name</option>
                    <option value="ACRONYM">Institutional Acronym</option>
                    <option value="PREVIOUS_LEGAL_NAME">Previous Legal Entity Name</option>
                  </select>
                </div>
              </div>
              <div className="flex justify-end">
                <button
                  type="submit"
                  disabled={submittingAlias || !newAliasName.trim()}
                  className="px-3.5 py-1.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold disabled:opacity-50 flex items-center gap-1.5"
                >
                  <Plus className="w-3.5 h-3.5" />
                  {submittingAlias ? 'Adding...' : 'Add Alias'}
                </button>
              </div>
            </form>

            <div className="flex justify-end pt-2">
              <button
                onClick={() => setAliasInst(null)}
                className="px-4 py-2 rounded-xl bg-slate-900 text-white font-semibold"
              >
                Close
              </button>
            </div>
          </div>
        </Modal>
      )}

      {/* Phase B: Create / Edit Organizational Unit Modal */}
      {isUnitModalOpen && (
        <Modal
          isOpen={true}
          onClose={() => {
            setIsUnitModalOpen(false);
            setEditingUnit(null);
          }}
          title={editingUnit ? `Edit Organizational Unit: ${editingUnit.code}` : 'Create AICTE Organizational Unit'}
          maxWidth="md"
        >
          <form onSubmit={handleSaveUnit} className="space-y-4 text-xs">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Unit Code *</label>
                <input
                  type="text"
                  required
                  disabled={!!editingUnit}
                  placeholder="e.g. RB, PGRC, AB"
                  value={unitCode}
                  onChange={(e) => setUnitCode(e.target.value.toUpperCase())}
                  className="w-full px-3 py-2 rounded-xl border border-slate-300 font-mono font-bold uppercase disabled:bg-slate-100 disabled:text-slate-500"
                />
              </div>
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Unit Type *</label>
                <select
                  value={unitType}
                  onChange={(e) => setUnitType(e.target.value as OrgUnitType)}
                  className="w-full px-3 py-2 rounded-xl border border-slate-300 text-slate-800 font-semibold"
                >
                  <option value="BUREAU">BUREAU (Autonomous Bureau)</option>
                  <option value="CELL">CELL (Specialized Grievance/Redressal Cell)</option>
                  <option value="REGIONAL_OFFICE">REGIONAL OFFICE (Territorial RO)</option>
                  <option value="OTHER">OTHER (Statutory Committee / Advisory)</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block font-semibold text-slate-700 mb-1">Unit Full Name *</label>
              <input
                type="text"
                required
                placeholder="e.g. Regulation Bureau"
                value={unitName}
                onChange={(e) => setUnitName(e.target.value)}
                className="w-full px-3 py-2 rounded-xl border border-slate-300"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Region Code (Optional)</label>
                <input
                  type="text"
                  placeholder="e.g. NORTH, WEST, SOUTH"
                  value={unitRegionCode}
                  onChange={(e) => setUnitRegionCode(e.target.value.toUpperCase())}
                  className="w-full px-3 py-2 rounded-xl border border-slate-300 font-mono"
                />
              </div>
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Parent Unit (Hierarchy)</label>
                <select
                  value={unitParentId}
                  onChange={(e) => setUnitParentId(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-slate-300 text-slate-800"
                >
                  <option value="">None (Top-Level Unit)</option>
                  {orgUnits
                    .filter((u) => !editingUnit || u.id !== editingUnit.id)
                    .map((u) => (
                      <option key={u.id} value={u.id}>
                        {u.code} — {u.name}
                      </option>
                    ))}
                </select>
              </div>
            </div>

            <div>
              <label className="block font-semibold text-slate-700 mb-1">Description / Functional Charter</label>
              <textarea
                rows={3}
                placeholder="Statutory scope and primary grievance jurisdiction of this unit..."
                value={unitDesc}
                onChange={(e) => setUnitDesc(e.target.value)}
                className="w-full px-3 py-2 rounded-xl border border-slate-300"
              />
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => {
                  setIsUnitModalOpen(false);
                  setEditingUnit(null);
                }}
                className="px-4 py-2 rounded-xl border border-slate-200 text-slate-600 font-semibold"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={savingUnit}
                className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold disabled:opacity-50"
              >
                {savingUnit ? 'Saving Unit...' : editingUnit ? 'Update Unit' : 'Create Unit'}
              </button>
            </div>
          </form>
        </Modal>
      )}

      {/* Phase B: Bureau Memberships Management Modal */}
      {selectedUnitForMembers && (
        <Modal
          isOpen={true}
          onClose={() => setSelectedUnitForMembers(null)}
          title={`Assigned Personnel: ${selectedUnitForMembers.code} (${selectedUnitForMembers.name})`}
          maxWidth="lg"
        >
          <div className="space-y-4 text-xs">
            <p className="text-slate-500">
              Assign and supervise authorized AICTE personnel for this organizational unit. Bureau memberships represent statutory cross-bureau authorities distinct from college-level roles.
            </p>

            {/* Current Members List */}
            <div className="bg-slate-50 rounded-xl border border-slate-200 overflow-hidden">
              <div className="p-3 border-b border-slate-200 flex items-center justify-between">
                <span className="font-bold text-slate-700 uppercase tracking-wider text-[10px]">
                  Active Personnel ({unitMembers.length})
                </span>
                {loadingMembers && <span className="text-[10px] text-blue-600 animate-pulse font-semibold">Loading...</span>}
              </div>
              <div className="max-h-52 overflow-y-auto divide-y divide-slate-100">
                {unitMembers.length === 0 ? (
                  <div className="p-4 text-center text-slate-400">No personnel currently assigned to this unit.</div>
                ) : (
                  unitMembers.map((m) => (
                    <div key={m.id} className="p-3 flex items-center justify-between hover:bg-white transition">
                      <div className="space-y-0.5">
                        <div className="font-semibold text-slate-900 flex items-center gap-2">
                          <span>{m.user_full_name || `User #${m.user_id}`}</span>
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-blue-50 text-blue-700 border border-blue-200">
                            {m.membership_role.replace(/_/g, ' ')}
                          </span>
                        </div>
                        <div className="text-[11px] text-slate-500 flex items-center gap-3">
                          <span>{m.user_email}</span>
                          {m.designation && <span>• {m.designation}</span>}
                          <span>• Assigned: {new Date(m.created_at).toLocaleDateString()}</span>
                        </div>
                      </div>
                      <button
                        onClick={() => handleRevokeMember(m.id)}
                        className="px-2.5 py-1 text-rose-600 hover:text-rose-700 hover:bg-rose-50 border border-rose-200 rounded-lg text-[10px] font-semibold transition"
                      >
                        Revoke
                      </button>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Assign User to Bureau Form */}
            <form onSubmit={handleAssignMember} className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-3">
              <span className="font-bold text-slate-800 block text-xs">Assign Personnel to this Unit</span>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Select User *</label>
                  <select
                    required
                    value={assignUserId}
                    onChange={(e) => setAssignUserId(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-slate-300 text-slate-800"
                  >
                    <option value="">Select a user...</option>
                    {users.map((u) => (
                      <option key={u.id} value={u.id}>
                        {u.full_name} ({u.email})
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Bureau Role *</label>
                  <select
                    value={assignRole}
                    onChange={(e) => setAssignRole(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-slate-300 text-slate-800 font-semibold"
                  >
                    <option value="BUREAU_HEAD">BUREAU HEAD (Bureau Director / Chief)</option>
                    <option value="BUREAU_OFFICER">BUREAU OFFICER (Scrutiny / Redressal)</option>
                    <option value="GRIEVANCE_CELL_OFFICER">GRIEVANCE CELL OFFICER</option>
                    <option value="REGIONAL_DIRECTOR">REGIONAL DIRECTOR</option>
                    <option value="LIAISON_OFFICER">LIAISON OFFICER</option>
                    <option value="ADVISOR">ADVISOR</option>
                  </select>
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Designation (Optional)</label>
                  <input
                    type="text"
                    placeholder="e.g. Scrutiny Officer"
                    value={assignDesignation}
                    onChange={(e) => setAssignDesignation(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-slate-300"
                  />
                </div>
              </div>
              <div className="flex justify-end">
                <button
                  type="submit"
                  disabled={assigningMember || !assignUserId}
                  className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold disabled:opacity-50 flex items-center gap-1.5"
                >
                  <Plus className="w-3.5 h-3.5" />
                  {assigningMember ? 'Assigning...' : 'Assign to Bureau'}
                </button>
              </div>
            </form>

            <div className="flex justify-end pt-2">
              <button
                onClick={() => setSelectedUnitForMembers(null)}
                className="px-4 py-2 rounded-xl bg-slate-900 text-white font-semibold"
              >
                Done
              </button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};
