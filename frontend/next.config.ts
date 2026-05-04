import type { NextConfig } from "next";

const securityHeaders = [
  // X-Frame-Options - prevent clickjacking
  {
    key: "X-Frame-Options",
    value: "DENY",
  },
  // X-Content-Type-Options - prevent MIME sniffing
  {
    key: "X-Content-Type-Options",
    value: "nosniff",
  },
  // X-XSS-Protection - legacy browser protection
  {
    key: "X-XSS-Protection",
    value: "1; mode=block",
  },
  // Referrer-Policy - control referrer info
  {
    key: "Referrer-Policy",
    value: "strict-origin-when-cross-origin",
  },
  // Permissions-Policy - limit browser features
  {
    key: "Permissions-Policy",
    value: "camera=(), microphone=(), geolocation=(), payment=(), usb=(), vr=()",
  },
  // Strict-Transport-Security (HSTS) - force HTTPS
  {
    key: "Strict-Transport-Security",
    value: "max-age=31536000; includeSubDomains; preload",
  },
  // Content-Security-Policy - prevent XSS and data injection
  {
    key: "Content-Security-Policy",
    value: [
      "default-src 'self'",
      "script-src 'self' 'unsafe-eval' 'unsafe-inline'",
      "style-src 'self' 'unsafe-inline'",
      "img-src 'self' blob: data: https:",
      "font-src 'self'",
      "connect-src 'self' https://*.aeiou.ai https://*.googleapis.com",
      "frame-ancestors 'none'",
      "base-uri 'self'",
      "form-action 'self'",
    ].join("; "),
  },
];

const nextConfig: NextConfig = {
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: true,
  },
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "**",
      },
    ],
  },
  // Security headers applied to all routes
  async headers() {
    return [
      {
        source: "/:path*",
        headers: securityHeaders,
      },
      {
        // Strict CSP for API routes
        source: "/api/:path*",
        headers: [
          ...securityHeaders,
          {
            key: "Cache-Control",
            value: "no-store, max-age=0",
          },
        ],
      },
    ];
  },
};

export default nextConfig;
