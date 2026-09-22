import type { NextConfig } from 'next';
const nextConfig: NextConfig = {
  output: 'standalone',
  poweredByHeader: false,
  skipTrailingSlashRedirect: true,
  async rewrites() {
    const backend = process.env.BACKEND_URL || 'http://127.0.0.1:8188';
    return [{ source: '/api/:path*', destination: `${backend}/api/:path*/` }, {source:'/admin/:path*',destination:`${backend}/admin/:path*/`},{source:'/django-static/:path*',destination:`${backend}/django-static/:path*`}];
  },
  async headers() {return [{source:'/:path*',headers:[{key:'X-Content-Type-Options',value:'nosniff'},{key:'Referrer-Policy',value:'same-origin'},{key:'X-Frame-Options',value:'DENY'}]}];}
};
export default nextConfig;
