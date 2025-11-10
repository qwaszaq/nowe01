import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts';
import { interpretQualityScore } from '../../lib/metricInterpretation';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';

interface QualityScoreCardProps {
  score: number;
  className?: string;
}

export const QualityScoreCard: React.FC<QualityScoreCardProps> = ({
  score,
  className = ''
}) => {
  const interpretation = interpretQualityScore(score);

  // Prepare data for circular progress
  const data = [
    { name: 'Score', value: score },
    { name: 'Remaining', value: 100 - score }
  ];

  // Color mapping
  const colorMap: Record<string, string> = {
    green: '#16a34a',
    blue: '#2563eb',
    yellow: '#ca8a04',
    red: '#dc2626'
  };

  const fillColor = colorMap[interpretation.color];
  const bgColor = '#e5e7eb';

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle>Analysis Quality Score</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex items-center justify-between">
          {/* Circular Progress Chart */}
          <div className="relative" style={{ width: 200, height: 200 }}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={data}
                  cx="50%"
                  cy="50%"
                  startAngle={90}
                  endAngle={-270}
                  innerRadius={60}
                  outerRadius={80}
                  dataKey="value"
                  stroke="none"
                >
                  <Cell fill={fillColor} />
                  <Cell fill={bgColor} />
                </Pie>
              </PieChart>
            </ResponsiveContainer>
            {/* Center Text */}
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-center">
                <div className="text-4xl font-bold text-gray-900">{score}</div>
                <div className="text-sm text-gray-500">/ 100</div>
              </div>
            </div>
          </div>

          {/* Score Details */}
          <div className="flex-1 ml-8">
            <div className="mb-4">
              <span
                className={`inline-block px-4 py-2 rounded-full text-lg font-semibold ${
                  interpretation.color === 'green'
                    ? 'bg-green-100 text-green-800'
                    : interpretation.color === 'blue'
                    ? 'bg-blue-100 text-blue-800'
                    : interpretation.color === 'yellow'
                    ? 'bg-yellow-100 text-yellow-800'
                    : 'bg-red-100 text-red-800'
                }`}
              >
                {interpretation.label}
              </span>
            </div>
            <p className="text-gray-700 text-base mb-4">{interpretation.description}</p>

            {/* Score Breakdown */}
            <div className="space-y-2 text-sm text-gray-600">
              <div className="flex items-center">
                <div className="w-3 h-3 rounded-full bg-green-500 mr-2"></div>
                <span>80-100: Excellent</span>
              </div>
              <div className="flex items-center">
                <div className="w-3 h-3 rounded-full bg-blue-500 mr-2"></div>
                <span>60-79: Good</span>
              </div>
              <div className="flex items-center">
                <div className="w-3 h-3 rounded-full bg-yellow-500 mr-2"></div>
                <span>40-59: Fair</span>
              </div>
              <div className="flex items-center">
                <div className="w-3 h-3 rounded-full bg-red-500 mr-2"></div>
                <span>0-39: Poor</span>
              </div>
            </div>
          </div>
        </div>

        {/* Additional Info */}
        <div className="mt-6 pt-6 border-t border-gray-200">
          <p className="text-sm text-gray-600">
            The quality score reflects the completeness and reliability of the financial data
            extracted from documents. Higher scores indicate more comprehensive and consistent
            data points.
          </p>
        </div>
      </CardContent>
    </Card>
  );
};
