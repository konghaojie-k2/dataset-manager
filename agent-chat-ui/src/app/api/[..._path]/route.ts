import { initApiPassthrough } from "langgraph-nextjs-api-passthrough";
import { NextRequest, NextResponse } from "next/server";

// This file acts as a proxy for requests to your LangGraph server.
// Read the [Going to Production](https://github.com/langchain-ai/agent-chat-ui?tab=readme-ov-file#going-to-production) section for more information.

const apiUrl = process.env.LANGGRAPH_API_URL ?? "http://localhost:2024";
const apiKey = process.env.LANGSMITH_API_KEY ?? undefined;

// 规范化消息格式：确保 human 消息的 content 是字符串
function normalizeMessages(messages: any[]): any[] {
  return messages.map((m: any) => {
    if (m.type === "human" && Array.isArray(m.content)) {
      const textBlocks = m.content.filter((c: any) => c.type === "text");
      if (textBlocks.length > 0) {
        return { ...m, content: textBlocks.map((c: any) => c.text).join(" ") };
      } else {
        return { ...m, content: "" };
      }
    }
    return m;
  });
}

async function POST(request: NextRequest) {
  return handleRequest(request, 'POST');
}

async function handleRequest(request: NextRequest, method: string) {
  const url = new URL(request.url);
  const path = url.pathname.replace('/api', '');
  const langgraphUrl = `${apiUrl}${path}${url.search}`;
  
  const headers: Record<string, string> = {};
  request.headers.forEach((value, key) => {
    if (key.toLowerCase() !== 'host') {
      headers[key] = value;
    }
  });
  if (apiKey) {
    headers['Authorization'] = `Bearer ${apiKey}`;
  }
  
  const options: RequestInit = {
    method,
    headers: {
      'Content-Type': 'application/json',
      ...headers,
    },
  };
  
  // 对于 POST/PUT/PATCH，需要处理请求体
  if (['POST', 'PUT', 'PATCH'].includes(method)) {
    try {
      const body = await request.json();
      
      // 规范化消息格式：确保 human 消息的 content 是字符串
      if (body.messages && Array.isArray(body.messages)) {
        body.messages = normalizeMessages(body.messages);
      }
      
      options.body = JSON.stringify(body);
    } catch (e) {
      // 如果不是 JSON，直接转发原始 body
      const body = await request.text();
      if (body) {
        options.body = body;
      }
    }
  }
  
  const response = await fetch(langgraphUrl, options);
  const responseData = await response.text();
  
  return new NextResponse(responseData, {
    status: response.status,
    headers: {
      'Content-Type': response.headers.get('Content-Type') || 'application/json',
    },
  });
}

async function GET(request: NextRequest) {
  return handleRequest(request, 'GET');
}

async function PUT(request: NextRequest) {
  return handleRequest(request, 'PUT');
}

async function PATCH(request: NextRequest) {
  return handleRequest(request, 'PATCH');
}

async function DELETE(request: NextRequest) {
  return handleRequest(request, 'DELETE');
}

async function OPTIONS(request: NextRequest) {
  return new NextResponse(null, {
    status: 200,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, PUT, PATCH, DELETE, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    },
  });
}

export { GET, POST, PUT, PATCH, DELETE, OPTIONS };
export const runtime = "edge";
