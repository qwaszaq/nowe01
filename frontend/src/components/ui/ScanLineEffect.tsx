/**
 * ScanLineEffect Component
 * Subtle scan-line animation for processing states
 */

interface ScanLineEffectProps {
  active?: boolean;
  className?: string;
}

export function ScanLineEffect({ active = true, className = '' }: ScanLineEffectProps) {
  if (!active) return null;

  return (
    <div className={`absolute inset-0 overflow-hidden pointer-events-none ${className}`}>
      {/* Animated scan line */}
      <div
        className="absolute inset-x-0 h-px bg-gradient-to-r from-transparent via-blue-400/30 to-transparent animate-scan-line"
        style={{
          animation: 'scanLine 3s linear infinite',
        }}
      />
      <style>{`
        @keyframes scanLine {
          0% {
            top: 0;
            opacity: 0;
          }
          10% {
            opacity: 1;
          }
          90% {
            opacity: 1;
          }
          100% {
            top: 100%;
            opacity: 0;
          }
        }
      `}</style>
    </div>
  );
}
