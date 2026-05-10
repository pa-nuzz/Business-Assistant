export function AnimatedLogo({ className = '', size = 32 }: { className?: string; size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 100 100"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      <rect x="20" y="45" width="8" height="35" rx="4" fill="#4F46E5">
        <animate attributeName="height" values="35;25;45;35" dur="3s" repeatCount="indefinite" />
        <animate attributeName="y" values="45;55;35;45" dur="3s" repeatCount="indefinite" />
      </rect>
      <rect x="35" y="30" width="8" height="50" rx="4" fill="#6366F1">
        <animate attributeName="height" values="50;35;55;50" dur="2.5s" repeatCount="indefinite" />
        <animate attributeName="y" values="30;45;25;30" dur="2.5s" repeatCount="indefinite" />
      </rect>
      <rect x="50" y="20" width="8" height="60" rx="4" fill="#4F46E5">
        <animate attributeName="height" values="60;40;70;60" dur="2s" repeatCount="indefinite" />
        <animate attributeName="y" values="20;40;10;20" dur="2s" repeatCount="indefinite" />
      </rect>
      <rect x="65" y="35" width="8" height="45" rx="4" fill="#6366F1">
        <animate attributeName="height" values="45;30;50;45" dur="2.7s" repeatCount="indefinite" />
        <animate attributeName="y" values="35;50;25;35" dur="2.7s" repeatCount="indefinite" />
      </rect>
      <rect x="80" y="50" width="8" height="30" rx="4" fill="#4F46E5">
        <animate attributeName="height" values="30;20;40;30" dur="3.2s" repeatCount="indefinite" />
        <animate attributeName="y" values="50;60;40;50" dur="3.2s" repeatCount="indefinite" />
      </rect>
      <defs>
        <linearGradient id="brandGradient" x1="0" y1="0" x2="100" y2="100" gradientUnits="userSpaceOnUse">
          <stop stopColor="#4F46E5" />
          <stop offset="1" stopColor="#6366F1" />
        </linearGradient>
      </defs>
    </svg>
  );
}
