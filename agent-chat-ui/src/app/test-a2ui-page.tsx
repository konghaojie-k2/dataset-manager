"use client";

import React, { useState } from "react";
import { StreamProvider } from "@/providers/Stream";
import { A2UIFormDebug } from "@/components/a2ui/A2UIFormDebug";
import { chatAPI } from "@/lib/api-extension";
import type { A2UISchema } from "@/lib/api-extension";

export default function TestA2UIPage(): React.ReactNode {
  const [testSchema] = useState<A2UISchema>({
    version: "1.0",
    form_id: "test",
    form_type: "search_refinement",
    title: "测试表单",
    description: "这是一个测试表单",
    fields: [
      {
        name: "industry",
        type: "select",
        label: "行业",
        placeholder: "请选择行业",
        options: [
          { value: "semiconductor", label: "半导体" },
          { value: "chemical", label: "化工" }
        ],
        required: true
      },
      {
        name: "quality",
        type: "range",
        label: "质量分数",
        validation: { min: 0, max: 100 },
        required: false
      }
    ],
    actions: [
      { id: "submit", type: "submit", label: "搜索", primary: true },
      { id: "cancel", type: "cancel", label: "取消" }
    ]
  });

  const handleSubmit = (data: any) => {
    console.log("Form submitted:", data);
    alert("表单提交成功！数据: " + JSON.stringify(data, null, 2));
  };

  return (
    <StreamProvider>
      <div className="min-h-screen bg-gray-100 p-8">
        <h1 className="text-2xl font-bold mb-4">A2UI 表单测试</h1>
        <A2UIFormDebug
          schema={testSchema}
          sessionId="test-session"
          onSubmit={handleSubmit}
        />
      </div>
    </StreamProvider>
  );
}
