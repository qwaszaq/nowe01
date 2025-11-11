/**
 * CaseStats Component
 * Display case statistics in cards
 */

import {
  DocumentTextIcon,
  CheckCircleIcon,
  ClockIcon,
  XCircleIcon,
  ChartBarIcon,
} from '@heroicons/react/24/outline';
import { useCaseStats } from '../../hooks/useCases';
import { LoadingSkeleton } from '../ui/LoadingSkeleton';
import { ErrorMessage } from '../ui/ErrorMessage';

interface CaseStatsProps {
  caseId: string;
}

interface StatCardProps {
  title: string;
  value: number | string;
  icon: React.ComponentType<{ className?: string }>;
  color: 'blue' | 'green' | 'yellow' | 'red' | 'purple';
  subtitle?: string;
}

function StatCard({ title, value, icon: Icon, color, subtitle }: StatCardProps) {
  const colorClasses = {
    blue: {
      bg: 'bg-gradient-to-br from-blue-50 to-blue-100',
      border: 'border-blue-200/50',
      icon: 'bg-blue-200/50 text-blue-600',
      title: 'text-blue-700',
      value: 'text-blue-900',
      hover: 'hover:from-blue-100 hover:to-blue-200'
    },
    green: {
      bg: 'bg-gradient-to-br from-emerald-50 to-emerald-100',
      border: 'border-emerald-200/50',
      icon: 'bg-emerald-200/50 text-emerald-600',
      title: 'text-emerald-700',
      value: 'text-emerald-900',
      hover: 'hover:from-emerald-100 hover:to-emerald-200'
    },
    yellow: {
      bg: 'bg-gradient-to-br from-amber-50 to-amber-100',
      border: 'border-amber-200/50',
      icon: 'bg-amber-200/50 text-amber-600',
      title: 'text-amber-700',
      value: 'text-amber-900',
      hover: 'hover:from-amber-100 hover:to-amber-200'
    },
    red: {
      bg: 'bg-gradient-to-br from-rose-50 to-rose-100',
      border: 'border-rose-200/50',
      icon: 'bg-rose-200/50 text-rose-600',
      title: 'text-rose-700',
      value: 'text-rose-900',
      hover: 'hover:from-rose-100 hover:to-rose-200'
    },
    purple: {
      bg: 'bg-gradient-to-br from-slate-50 to-slate-100',
      border: 'border-slate-200/50',
      icon: 'bg-slate-200/50 text-slate-600',
      title: 'text-slate-700',
      value: 'text-slate-900',
      hover: 'hover:from-slate-100 hover:to-slate-200'
    },
  };

  const classes = colorClasses[color];

  return (
    <div className={`group relative ${classes.bg} border ${classes.border} rounded-2xl p-6 shadow-lg transition-all duration-300 hover:shadow-xl hover:scale-105 overflow-hidden`}>
      <div className={`absolute inset-0 bg-gradient-to-br opacity-0 group-hover:opacity-100 transition-opacity duration-300 ${classes.hover}`}></div>
      <div className="relative z-10">
        <div className="flex items-center justify-between mb-3">
          <p className={`text-sm font-semibold ${classes.title}`}>{title}</p>
          <div className={`p-3 rounded-xl backdrop-blur-sm ${classes.icon}`}>
            <Icon className="h-6 w-6" />
          </div>
        </div>
        <p className={`text-4xl font-bold ${classes.value} mb-1`}>{value}</p>
        {subtitle && <p className={`text-xs font-medium ${classes.title} opacity-75`}>{subtitle}</p>}
      </div>
    </div>
  );
}

export function CaseStats({ caseId }: CaseStatsProps) {
  const { data: stats, isLoading, error, refetch } = useCaseStats(caseId);

  if (isLoading) {
    return <LoadingSkeleton variant="stats" count={5} />;
  }

  if (error) {
    return <ErrorMessage error={error} onRetry={refetch} variant="inline" />;
  }

  if (!stats) {
    return null;
  }

  // Calculate processing count from all processing states
  const processingCount = (stats.pending || 0) + (stats.extracting || 0) +
                         (stats.chunking || 0) + (stats.embedding || 0) +
                         (stats.storing || 0);

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
      <StatCard
        title="Total Documents"
        value={stats.total_documents || 0}
        icon={DocumentTextIcon}
        color="blue"
      />

      <StatCard
        title="Completed"
        value={stats.completed || 0}
        icon={CheckCircleIcon}
        color="green"
      />

      <StatCard
        title="Processing"
        value={processingCount}
        icon={ClockIcon}
        color="yellow"
      />

      <StatCard
        title="Failed"
        value={stats.failed || 0}
        icon={XCircleIcon}
        color="red"
      />

      <StatCard
        title="Success Rate"
        value={`${(stats.success_rate || 0).toFixed(1)}%`}
        icon={ChartBarIcon}
        color="purple"
      />
    </div>
  );
}
