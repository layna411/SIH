import React, { useState } from 'react';
import { Mail, Phone, MapPin, Send, CheckCircle2 } from 'lucide-react';

export const ContactPage: React.FC = () => {
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitted(true);
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-16">
      <div className="text-center mb-12">
        <h1 className="text-3xl sm:text-4xl font-extrabold text-slate-900">Support & Helpdesk</h1>
        <p className="mt-3 text-base text-slate-600">
          Reach out to the EduResolve technical desk or locate institutional escalation avenues.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div className="bg-white p-6 sm:p-8 rounded-2xl border border-slate-200/80 shadow-sm">
          <h2 className="text-lg font-bold text-slate-900 mb-6">Contact Grievance Central</h2>
          
          <div className="space-y-4 text-xs text-slate-600">
            <div className="flex items-center gap-3 p-3 rounded-xl bg-slate-50 border border-slate-100">
              <Mail className="w-4 h-4 text-blue-600 shrink-0" />
              <div>
                <p className="font-semibold text-slate-800">Email Support</p>
                <p>support@eduresolve.ai</p>
              </div>
            </div>

            <div className="flex items-center gap-3 p-3 rounded-xl bg-slate-50 border border-slate-100">
              <Phone className="w-4 h-4 text-emerald-600 shrink-0" />
              <div>
                <p className="font-semibold text-slate-800">Helpline Hours</p>
                <p>Monday - Friday, 9:00 AM - 6:00 PM IST</p>
              </div>
            </div>

            <div className="flex items-center gap-3 p-3 rounded-xl bg-slate-50 border border-slate-100">
              <MapPin className="w-4 h-4 text-purple-600 shrink-0" />
              <div>
                <p className="font-semibold text-slate-800">Central Architecture Lab</p>
                <p>New Delhi & Regional Educational Hubs</p>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 sm:p-8 rounded-2xl border border-slate-200/80 shadow-sm">
          <h2 className="text-lg font-bold text-slate-900 mb-4">Inquiry / Escalation Query</h2>
          {submitted ? (
            <div className="py-8 text-center text-xs text-emerald-700 bg-emerald-50 p-4 rounded-xl border border-emerald-200">
              <CheckCircle2 className="w-8 h-8 text-emerald-600 mx-auto mb-2" />
              <p className="font-semibold">Message Received</p>
              <p className="text-slate-500 mt-1">Our central support desk will respond within 1 business day.</p>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4 text-xs">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Your Name</label>
                <input
                  type="text"
                  required
                  placeholder="Full name"
                  className="w-full px-3.5 py-2 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Email Address</label>
                <input
                  type="email"
                  required
                  placeholder="you@domain.edu"
                  className="w-full px-3.5 py-2 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Message</label>
                <textarea
                  rows={4}
                  required
                  placeholder="How can we assist you?"
                  className="w-full px-3.5 py-2 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
                ></textarea>
              </div>
              <button
                type="submit"
                className="w-full py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold transition flex items-center justify-center gap-2"
              >
                Send Message
                <Send className="w-3.5 h-3.5" />
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
};
