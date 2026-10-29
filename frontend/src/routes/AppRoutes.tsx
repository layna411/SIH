import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { PublicLayout } from '../layouts/PublicLayout';
import { DashboardLayout } from '../layouts/DashboardLayout';
import { ProtectedRoute } from './ProtectedRoute';

// Public pages
import { LandingPage } from '../pages/public/LandingPage';
import { AboutPage } from '../pages/public/AboutPage';
import { HowItWorksPage } from '../pages/public/HowItWorksPage';
import { FeaturesPage } from '../pages/public/FeaturesPage';
import { PrivacyPage } from '../pages/public/PrivacyPage';
import { ContactPage } from '../pages/public/ContactPage';
import { TrackGrievancePage } from '../pages/public/TrackGrievancePage';
import { LoginPage } from '../pages/auth/LoginPage';
import { RegisterPage } from '../pages/auth/RegisterPage';
import { AcceptInvitationPage } from '../pages/auth/AcceptInvitationPage';
import { VerifyEmailPage } from '../pages/auth/VerifyEmailPage';

import { NotFoundPage } from '../pages/public/NotFoundPage';

// Student pages
import { StudentDashboard } from '../pages/student/StudentDashboard';
import { SubmitGrievancePage } from '../pages/student/SubmitGrievancePage';
import { GrievanceDetailPage } from '../pages/student/GrievanceDetailPage';
import { ProfilePage } from '../pages/student/ProfilePage';

// Officer pages
import { OfficerDashboard } from '../pages/officer/OfficerDashboard';

// Institution Head pages
import { HeadDashboard } from '../pages/institution/HeadDashboard';

// Regulatory Admin pages
import { RegulatoryDashboard } from '../pages/regulatory/RegulatoryDashboard';

// Super Admin pages
import { SuperAdminDashboard } from '../pages/superadmin/SuperAdminDashboard';

// AICTE Case Management pages (Step 7, Phase C)
import { AICTEIntegratedDashboard } from '../pages/aicte/AICTEIntegratedDashboard';
import { AICTECaseList } from '../pages/aicte/AICTECaseList';
import { AICTECaseDetail } from '../pages/aicte/AICTECaseDetail';
import { AICTEInstitutionProfile } from '../pages/aicte/AICTEInstitutionProfile';
import { AICTEOverlapQueue } from '../pages/aicte/AICTEOverlapQueue';
import { AICTEOverlapDetail } from '../pages/aicte/AICTEOverlapDetail';
import { AICTETransferQueue } from '../pages/aicte/AICTETransferQueue';
import { AICTENotificationCenter } from '../pages/aicte/AICTENotificationCenter';

export const AppRoutes: React.FC = () => {
  return (
    <Routes>
      {/* Public Pages */}
      <Route element={<PublicLayout />}>
        <Route path="/" element={<LandingPage />} />
        <Route path="/about" element={<AboutPage />} />
        <Route path="/how-it-works" element={<HowItWorksPage />} />
        <Route path="/features" element={<FeaturesPage />} />
        <Route path="/privacy" element={<PrivacyPage />} />
        <Route path="/contact" element={<ContactPage />} />
        <Route path="/track" element={<TrackGrievancePage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/accept-invitation" element={<AcceptInvitationPage />} />
        <Route path="/verify-email" element={<VerifyEmailPage />} />
      </Route>

      {/* Protected Common Profile (All Authenticated Roles) */}
      <Route element={<ProtectedRoute allowedRoles={['STUDENT', 'COLLEGE_OFFICER', 'INSTITUTION_HEAD', 'REGULATORY_ADMIN', 'SUPER_ADMIN']} />}>
        <Route element={<DashboardLayout />}>
          <Route path="/profile" element={<ProfilePage />} />
        </Route>
      </Route>

      {/* Protected Student Portal */}
      <Route element={<ProtectedRoute allowedRoles={['STUDENT', 'SUPER_ADMIN']} />}>
        <Route element={<DashboardLayout />}>
          <Route path="/student" element={<StudentDashboard />} />
          <Route path="/student/submit" element={<SubmitGrievancePage />} />
          <Route path="/student/grievances/:id" element={<GrievanceDetailPage />} />
          <Route path="/student/profile" element={<ProfilePage />} />
        </Route>
      </Route>

      {/* Protected Officer Portal */}
      <Route element={<ProtectedRoute allowedRoles={['COLLEGE_OFFICER', 'SUPER_ADMIN']} />}>
        <Route element={<DashboardLayout />}>
          <Route path="/officer" element={<OfficerDashboard />} />
          <Route path="/officer/reports" element={<OfficerDashboard />} />
        </Route>
      </Route>

      {/* Protected Institution Head Portal */}
      <Route element={<ProtectedRoute allowedRoles={['INSTITUTION_HEAD', 'SUPER_ADMIN']} />}>
        <Route element={<DashboardLayout />}>
          <Route path="/head" element={<HeadDashboard />} />
          <Route path="/head/escalations" element={<HeadDashboard />} />
          <Route path="/head/officers" element={<HeadDashboard />} />
        </Route>
      </Route>

      {/* Protected Regulatory Admin Portal */}
      <Route element={<ProtectedRoute allowedRoles={['REGULATORY_ADMIN', 'SUPER_ADMIN']} />}>
        <Route element={<DashboardLayout />}>
          <Route path="/regulatory" element={<RegulatoryDashboard />} />
        </Route>
      </Route>

      {/* Protected Super Admin Portal */}
      <Route element={<ProtectedRoute allowedRoles={['SUPER_ADMIN']} />}>
        <Route element={<DashboardLayout />}>
          <Route path="/admin" element={<SuperAdminDashboard />} />
          <Route path="/admin/institutions" element={<SuperAdminDashboard />} />
          <Route path="/admin/users" element={<SuperAdminDashboard />} />
          <Route path="/admin/categories" element={<SuperAdminDashboard />} />
          <Route path="/admin/bureaus" element={<SuperAdminDashboard />} />
        </Route>
      </Route>

      {/* Protected AICTE Case Management & Cross-Bureau Monitoring */}
      <Route element={<ProtectedRoute allowedRoles={['REGULATORY_ADMIN', 'SUPER_ADMIN']} allowBureauMembers={true} />}>
        <Route element={<DashboardLayout />}>
          <Route path="/aicte" element={<AICTEIntegratedDashboard />} />
          <Route path="/aicte/cases" element={<AICTECaseList />} />
          <Route path="/aicte/cases/:id" element={<AICTECaseDetail />} />
          <Route path="/aicte/institutions/:id" element={<AICTEInstitutionProfile />} />
          <Route path="/aicte/overlaps" element={<AICTEOverlapQueue />} />
          <Route path="/aicte/overlaps/:id" element={<AICTEOverlapDetail />} />
          <Route path="/aicte/transfers" element={<AICTETransferQueue />} />
          <Route path="/aicte/notifications" element={<AICTENotificationCenter />} />
        </Route>
      </Route>

      {/* Catch-all Not Found */}
      <Route path="*" element={<PublicLayout />}>
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
};
