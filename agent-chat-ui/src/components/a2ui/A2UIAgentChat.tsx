import { useState, useEffect, useCallback } from "react";
import { useStreamContext } from "@/providers/Stream";
import { Message } from "@langchain/langgraph-sdk";
import { A2UIForm } from "./A2UIForm";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Loader2, Send, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";
import type { A2UISchema, ChatResponse } from "@/lib/api-extension";
import { chatAPI } from "@/lib/api-extension";

interface A2UIChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  ui_form?: {
    schema: A2UISchema;
    clarification_reason: string;
  };
}

interface A2UIAgentChatProps {
  className?: string;
  onDatasetSelect?: (dataset: any) => void;
}

export function A2UIAgentChat({ className, onDatasetSelect }: A2UIAgentChatProps) {
  const { submit, isLoading, messages: langgraphMessages } = useStreamContext();
  const [input, setInput] = useState("");
  const [chatMessages, setChatMessages] = useState<A2UIChatMessage[]>([]);
  const [pendingForm, setPendingForm] = useState<{
    schema: A2UISchema;
    clarification_reason: string;
    relatedMessageId: string;
  } | null>(null);
  const [sessionId] = useState(() => `a2ui-${Date.now()}`);

  const processLangGraphMessages = useCallback(() => {
    if (!langgraphMessages || langgraphMessages.length === 0) return;

    const newMessages: A2UIChatMessage[] = [];
    const toolCallIdToResult = new Map<string, any>();

    // 第一遍：收集所有工具调用的结果
    langgraphMessages.forEach((msg) => {
      if (msg.type === "tool") {
        const toolCallId = msg.tool_call_id;
        const content = msg.content;
        if (toolCallId && content) {
          try {
            const parsed = typeof content === "string" ? JSON.parse(content) : content;
            toolCallIdToResult.set(toolCallId, parsed);
          } catch {
            toolCallIdToResult.set(toolCallId, content);
          }
        }
      }
    });

    // 第二遍：处理消息
    langgraphMessages.forEach((msg) => {
      if (msg.type === "human") {
        newMessages.push({
          id: msg.id || `msg-${Date.now()}-${Math.random()}`,
          role: "user",
          content: typeof msg.content === "string" ? msg.content : JSON.stringify(msg.content)
        });
      } else if (msg.type === "ai" || msg.type === "tool") {
        let content = "";
        let ui_form = undefined;

        const messageContent = msg.content;
        if (typeof messageContent === "string") {
          content = messageContent;
        } else if (Array.isArray(messageContent)) {
          content = messageContent
            .map((c) => {
              if (typeof c === "string") return c;
              if (c.type === "text") return c.text;
              return JSON.stringify(c);
            })
            .join("\n");
        }

        // 检查工具调用结果（对于 ai 类型的消息）
        if (msg.type === "ai" && msg.tool_calls && msg.tool_calls.length > 0) {
          for (const toolCall of msg.tool_calls) {
            if (toolCall.name === "clarify_intent") {
              const toolResult = toolCallIdToResult.get(toolCall.id);
              if (toolResult) {
                try {
                  const resultContent = typeof toolResult === "string" ? JSON.parse(toolResult) : toolResult;
                  if (resultContent.type === "ui_form" && resultContent.form_schema) {
                    ui_form = {
                      schema: resultContent.form_schema,
                      clarification_reason: resultContent.clarification_reason || ""
                    };
                    content = resultContent.message || "请完善以下信息";
                  }
                } catch (e) {
                  console.error("Failed to parse tool result:", e);
                }
              }
            }
          }
        }

        // 对于 tool 类型的消息，直接解析内容
        if (msg.type === "tool") {
          try {
            const resultContent = typeof content === "string" ? JSON.parse(content) : content;
            if (resultContent.type === "ui_form" && resultContent.form_schema) {
              ui_form = {
                schema: resultContent.form_schema,
                clarification_reason: resultContent.clarification_reason || ""
              };
              content = resultContent.message || "请完善以下信息";
            }
          } catch {
            // 不是 JSON，保持原样
          }
        }

        newMessages.push({
          id: msg.id || `msg-${Date.now()}-${Math.random()}`,
          role: "assistant",
          content,
          ui_form
        });
      }
    });

    setChatMessages(newMessages);
  }, [langgraphMessages]);

  useEffect(() => {
    processLangGraphMessages();
  }, [langgraphMessages, processLangGraphMessages]);

  const handleAgentSubmit = (content: string) => {
    if (!submit || !content.trim()) return;

    const newMessage: Message = { type: "human", content: content.trim() };
    submit(
      { messages: [newMessage] },
      {
        streamMode: ["values"],
        streamSubgraphs: true,
        streamResumable: true,
      },
    );
    setInput("");
  };

  const handleFormSubmit = async (formData: Record<string, any>) => {
    if (!pendingForm) return;

    setPendingForm(null);

    try {
      const response = await chatAPI.submitForm(
        sessionId,
        pendingForm.schema.form_id || "default",
        formData
      );

      const assistantMessage: A2UIChatMessage = {
        id: `msg-${Date.now()}-${Math.random()}`,
        role: "assistant",
        content: response.message || "搜索完成",
        ui_form: undefined
      };

      setChatMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      console.error("表单提交失败:", error);
      const errorMessage: A2UIChatMessage = {
        id: `msg-${Date.now()}-${Math.random()}`,
        role: "assistant",
        content: "表单提交失败，请重试"
      };
      setChatMessages((prev) => [...prev, errorMessage]);
    }
  };

  const handleFormCancel = () => {
    setPendingForm(null);
  };

  const handleDatasetClick = (dataset: any) => {
    onDatasetSelect?.(dataset);
  };

  return (
    <Card className={cn("flex flex-col h-full", className)}>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-primary" />
          智能数据集搜索
        </CardTitle>
        <CardDescription>
          描述您需要的数据集，AI 会自动理解并搜索
        </CardDescription>
      </CardHeader>

      <CardContent className="flex-1 flex flex-col overflow-hidden p-0">
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {chatMessages.length === 0 && (
            <div className="text-center text-muted-foreground py-8">
              <Sparkles className="h-12 w-12 mx-auto mb-3 opacity-50" />
              <p className="text-sm">输入您要搜索的数据集描述</p>
              <p className="text-xs mt-1">例如：&quot;半导体行业的高质量传感器数据&quot;</p>
            </div>
          )}

          {chatMessages.map((message) => (
            <div
              key={message.id}
              className={cn(
                "flex flex-col gap-2",
                message.role === "user" ? "items-end" : "items-start"
              )}
            >
              <div
                className={cn(
                  "max-w-[85%] rounded-lg px-4 py-2",
                  message.role === "user"
                    ? "bg-primary text-primary-foreground"
                    : "bg-muted"
                )}
              >
                <p className="text-sm whitespace-pre-wrap">{message.content}</p>
              </div>

              {message.ui_form && (
                <div className="w-full max-w-[90%]">
                  <A2UIForm
                    schema={message.ui_form.schema}
                    sessionId={sessionId}
                    onSubmit={handleFormSubmit}
                    onCancel={handleFormCancel}
                  />
                </div>
              )}
            </div>
          ))}

          {isLoading && (
            <div className="flex items-center gap-2 text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span className="text-sm">AI 思考中...</span>
            </div>
          )}
        </div>

        <div className="border-t p-4">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleAgentSubmit(input);
            }}
            className="flex gap-2"
          >
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="描述您需要的数据集..."
              disabled={isLoading}
              className="flex-1"
            />
            <Button type="submit" disabled={isLoading || !input.trim()}>
              <Send className="h-4 w-4" />
            </Button>
          </form>
        </div>
      </CardContent>
    </Card>
  );
}
