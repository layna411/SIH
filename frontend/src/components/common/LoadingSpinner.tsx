import React from 'react';
import { Loader2 } from 'lucide-react';

export const LoadingSpinner: React.FC<{ message?: string; className?: string }> = ({
  message = 'Loading...',
  className = 'py-12',
}) => {
  return (
    <div className={`flex flex-col items-center justify-center ${className}`}>
      <Loader2 className="w-8 h-8 text-blue-600 animate-spin mb-3" />
      <p className="text-sm text-slate-500 font-medium">{message}</p>
    </div>
  );
};
