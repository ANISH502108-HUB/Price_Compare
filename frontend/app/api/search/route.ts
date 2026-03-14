import { NextRequest } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const backendBaseUrl = process.env.BACKEND_BASE_URL ?? "http://127.0.0.1:8000";

export async function GET(request: NextRequest): Promise<Response> {
  const item = request.nextUrl.searchParams.get("item")?.trim();
  const pincode = request.nextUrl.searchParams.get("pincode")?.trim();

  if (!item || !pincode) {
    return Response.json(
      { error: "Both item and pincode are required." },
      { status: 400 },
    );
  }

  const upstreamUrl = new URL("/search", backendBaseUrl);
  upstreamUrl.searchParams.set("item", item);
  upstreamUrl.searchParams.set("pincode", pincode);

  let upstream: Response;

  try {
    upstream = await fetch(upstreamUrl, {
      headers: { Accept: "text/event-stream" },
      cache: "no-store",
    });
  } catch {
    return Response.json(
      {
        error: "Backend search stream unavailable.",
        status: 502,
      },
      { status: 502 },
    );
  }

  if (!upstream.ok || !upstream.body) {
    return Response.json(
      {
        error: "Backend search stream unavailable.",
        status: upstream.status,
      },
      { status: 502 },
    );
  }

  return new Response(upstream.body, {
    status: upstream.status,
    headers: {
      "Content-Type": "text/event-stream; charset=utf-8",
      "Cache-Control": "no-cache, no-transform",
      Connection: "keep-alive",
      "X-Accel-Buffering": "no",
    },
  });
}
