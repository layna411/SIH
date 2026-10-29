import React from 'react';
import { Lock, EyeOff, ShieldCheck, Database, Key } from 'lucide-react';

export const PrivacyPage: React.FC = () => {
  return (
    <div className="max-w-4xl mx-auto px-4 py-16">
      <div className="text-center mb-12">
        <h1 className="text-3xl sm:text-4xl font-extrabold text-slate-900">Privacy & Confidentiality</h1>
        <p className="mt-3 text-base text-slate-600">
          How EduResolve AI protects student identity, institutional data boundaries, and sensitive evidence.
        </p>
      </div>

      <div className="space-y-8 bg-white p-8 rounded-2xl border border-slate-200/80 shadow-sm text-sm text-slate-600 leading-relaxed">
        <section>
          <h2 className="text-base font-bold text-slate-900 mb-2 flex items-center gap-2">
            <EyeOff className="w-4 h-4 text-blue-600" />
            Confidential Reporting Mode
          </h2>
          <p>
            When submitting sensitive grievances (such as misconduct, harassment, or whistleblowing), students can activate <strong>Confidential Reporting</strong>. In this mode, the student's name, email, and enrollment ID are automatically masked on general review dashboards, accessible only to designated senior inquiry officers or super administrators.
          </p>
        </section>

        <section>
          <h2 className="text-base font-bold text-slate-900 mb-2 flex items-center gap-2">
            <Lock className="w-4 h-4 text-emerald-600" />
            No Anonymous Misuse
          </h2>
          <p>
            To prevent fabricated allegations or harassment, complaints require authenticated student registration with institutional verification. However, identifying tokens are strictly shielded from public views.
          </p>
        </section>

        <section>
          <h2 className="text-base font-bold text-slate-900 mb-2 flex items-center gap-2">
            <Database className="w-4 h-4 text-purple-600" />
            Private Storage Architecture
          </h2>
          <p>
            Supporting documents (PDFs, images, documents) are stored in restricted private server directories outside public static web roots. Every download request enforces database authorization checks against the user's role and tenant membership before serving file bytes.
          </p>
        </section>

        <section>
          <h2 className="text-base font-bold text-slate-900 mb-2 flex items-center gap-2">
            <Key className="w-4 h-4 text-indigo-600" />
            Argon2 Password Protection
          </h2>
          <p>
            User credentials are encrypted using memory-hard Argon2 password hashing. JWT access tokens are cryptographically signed with short expirations and automatic session revocation upon logout.
          </p>
        </section>
      </div>
    </div>
  );
};
