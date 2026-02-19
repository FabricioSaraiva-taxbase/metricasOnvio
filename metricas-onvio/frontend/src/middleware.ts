import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export function middleware(request: NextRequest) {
    // Check if request is for /api
    if (request.nextUrl.pathname.startsWith('/api/')) {
        // Get backend URL from env or default to localhost
        const backendUrl = process.env.API_URL || 'http://localhost:8000';

        // Construct the new URL
        // backendUrl does not have trailing slash, pathname starts with /
        const targetUrl = new URL(request.nextUrl.pathname + request.nextUrl.search, backendUrl);

        // Rewrite the request to the backend
        return NextResponse.rewrite(targetUrl);
    }
}

export const config = {
    matcher: '/api/:path*',
}
