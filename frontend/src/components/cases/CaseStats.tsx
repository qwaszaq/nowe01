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
    blue: 'bg-blue-50 text-blue-600',
    green: 'bg-green-50 text-green-600',
    yellow: 'bg-yellow-50 text-yellow-600',
    red: 'bg-red-50 text-red-600',
    purple: 'bg-purple-50 text-purple-600',
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
      <div className="flex items-center justify-between mb-2">
        <p className="text-sm font-medium text-gray-600">{title}</p>
        <div className={`p-2 rounded-lg ${colorClasses[color]}`}>
          <Icon className="h-5 w-5" />
        </div>
      </div>
      <p className="text-3xl font-bold text-gray-900">{value}</p>
      {subtitle && <p className="text-sm text-gray-500 mt-1">{subtitle}</p>}
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
