/**
 * Activity Log Component
 * Displays a timeline of activities for a case
 */

import { useEffect, useState } from 'react';
import {
  ClockIcon,
  DocumentTextIcon,
  ArrowUpTrayIcon,
  CheckCircleIcon,
  ExclamationCircleIcon,
  MagnifyingGlassIcon,
  FolderIcon,
} from '@heroicons/react/24/outline';
import { formatDistanceToNow } from 'date-fns';
import { Spinner } from '../ui/LoadingSkeleton';

interface Activity {
  id: string;
  type: 'case_created' | 'case_updated' | 'document_uploaded' | 'document_processed' | 'document_failed' | 'search_performed';
  title: string;
  description: string;
  timestamp: string;
  metadata?: Record<string, any>;
}

interface ActivityLogProps {
  caseId: string;
}

export function ActivityLog({ caseId }: ActivityLogProps) {
  const [activities, setActivities] = useState<Activity[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchActivities();

    // Poll for new activities every 5 seconds
    const interval = setInterval(fetchActivities, 5000);

    return () => clearInterval(interval);
  }, [caseId]);

  const fetchActivities = async () => {
    try {
      const response = await fetch(`http://localhost:8000/api/v1/cases/${caseId}/activities`);
      if (response.ok) {
        const data = await response.json();
        setActivities(data.activities || []);
      }
    } catch (error) {
      console.error('Error fetching activities:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const getActivityIcon = (type: Activity['type']) => {
    switch (type) {
      case 'case_created':
        return <FolderIcon className="h-5 w-5" />;
      case 'case_updated':
        return <FolderIcon className="h-5 w-5" />;
      case 'document_uploaded':
        return <ArrowUpTrayIcon className="h-5 w-5" />;
      case 'document_processed':
        return <CheckCircleIcon className="h-5 w-5" />;
      case 'document_failed':
        return <ExclamationCircleIcon className="h-5 w-5" />;
      case 'search_performed':
        return <MagnifyingGlassIcon className="h-5 w-5" />;
      default:
        return <ClockIcon className="h-5 w-5" />;
    }
  };

  const getActivityColor = (type: Activity['type']) => {
    switch (type) {
      case 'case_created':
        return 'from-blue-500 to-blue-600';
      case 'case_updated':
        return 'from-slate-500 to-slate-600';
      case 'document_uploaded':
        return 'from-purple-500 to-purple-600';
      case 'document_processed':
        return 'from-green-500 to-green-600';
      case 'document_failed':
        return 'from-red-500 to-red-600';
      case 'search_performed':
        return 'from-cyan-500 to-cyan-600';
      default:
        return 'from-gray-500 to-gray-600';
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Spinner size="lg" />
        <span className="ml-3 text-gray-600">Loading activities...</span>
      </div>
    );
  }

  if (activities.length === 0) {
    return (
      <div className="text-center py-12">
        <ClockIcon className="h-12 w-12 mx-auto mb-3 text-gray-400" />
        <h3 className="text-lg font-semibold text-gray-700 mb-2">No Activity Yet</h3>
        <p className="text-gray-500">Case activities will appear here as they happen.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-gray-800 flex items-center">
          <ClockIcon className="h-5 w-5 mr-2 text-gray-600" />
          Activity Timeline
        </h3>
        <span className="text-sm text-gray-500">{activities.length} activities</span>
      </div>

      <div className="relative">
        {/* Timeline Line */}
        <div className="absolute left-6 top-0 bottom-0 w-0.5 bg-gradient-to-b from-blue-200 via-purple-200 to-transparent"></div>

        {/* Activities */}
        <div className="space-y-6">
          {activities.map((activity, index) => (
            <div key={activity.id} className="relative flex gap-4 group">
              {/* Icon Circle */}
              <div className={`relative z-10 flex-shrink-0 w-12 h-12 rounded-full bg-gradient-to-br ${getActivityColor(activity.type)} flex items-center justify-center text-white shadow-lg group-hover:shadow-xl group-hover:scale-110 transition-all duration-200`}>
                {getActivityIcon(activity.type)}
              </div>

              {/* Activity Card */}
              <div className="flex-1 bg-white rounded-xl border border-gray-200 shadow-sm hover:shadow-md transition-all duration-200 overflow-hidden group-hover:border-blue-300">
                <div className="p-4">
                  <div className="flex items-start justify-between mb-2">
                    <h4 className="font-semibold text-gray-800 group-hover:text-blue-700 transition-colors">
                      {activity.title}
                    </h4>
                    <span className="text-xs text-gray-500 whitespace-nowrap ml-2">
                      {formatDistanceToNow(new Date(activity.timestamp), { addSuffix: true })}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600 leading-relaxed">{activity.description}</p>

                  {/* Metadata */}
                  {activity.metadata && Object.keys(activity.metadata).length > 0 && (
                    <div className="mt-3 pt-3 border-t border-gray-100">
                      <div className="flex flex-wrap gap-2">
                        {Object.entries(activity.metadata).map(([key, value]) => (
                          <span
                            key={key}
                            className="inline-flex items-center px-2 py-1 rounded-lg text-xs font-medium bg-gray-100 text-gray-700"
                          >
                            <span className="font-semibold mr-1">{key}:</span>
                            {String(value)}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
