import { useState, useRef, useEffect } from "react";
import { A2UIForm, type A2UISchema } from "./A2UIForm";
import { chatAPI, type ChatResponse, type Dataset } from "@/lib/api-extension";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Loader2, Send, Sparkles, X } from "lucide-react";
import { cn } from "@/lib/utils";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  datasets?: Dataset[];
  a2ui_form?: A2UISchema;
  isLoading?: boolean;
}

interface A2UIChatPanelProps {
  className?: string;
  onDatasetSelect?: (dataset: Dataset) => void;
}

export function A2UIChatPanel({ className, onDatasetSelect }: A2UIChatPanelProps) {
  const [sessionId] = useState(() => `a2ui-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [currentForm, setCurrentForm] = useState<A2UISchema | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, currentForm]);

  const handleSendMessage = async (content: string) => {
    if (!content.trim() || isLoading) return;

    const userMessage: Message = {
      id: `msg-${Date.now()}`,
      role: "user",
      content: content.trim()
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      const response = await chatAPI.send(sessionId, content.trim());

      if (response.type === "clarification_needed" && response.a2ui_form) {
        const assistantMessage: Message = {
          id: `msg-${Date.now()}`,
          role: "assistant",
          content: response.message,
          a2ui_form: response.a2ui_form
        };
        setMessages((prev) => [...prev, assistantMessage]);
        setCurrentForm(response.a2ui_form);
      } else {
        const assistantMessage: Message = {
          id: `msg-${Date.now()}`,
          role: "assistant",
          content: response.message,
          datasets: response.datasets
        };
        setMessages((prev) => [...prev, assistantMessage]);
      }
    } catch (error) {
      console.error("发送消息失败:", error);
      const errorMessage: Message = {
        id: `msg-${Date.now()}`,
        role: "assistant",
        content: "抱歉，处理您的请求时出错了。请重试。"
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFormSubmit = async (response: ChatResponse) => {
    setCurrentForm(null);

    const assistantMessage: Message = {
      id: `msg-${Date.now()}`,
      role: "assistant",
      content: response.message,
      datasets: response.datasets
    };

    setMessages((prev) => [...prev, assistantMessage]);
  };

  const handleFormCancel = () => {
    setCurrentForm(null);
  };

  const handleDatasetClick = (dataset: Dataset) => {
    onDatasetSelect?.(dataset);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    handleSendMessage(input);
  };

  return (
    <Card className={cn("flex flex-col h-full max-w-2xl mx-auto", className)}>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-primary" />
          数据集智能搜索
        </CardTitle>
        <CardDescription>
          告诉我您需要什么类型的数据集，我会帮您找到最合适的
        </CardDescription>
      </CardHeader>

      <CardContent className="flex-1 flex flex-col overflow-hidden p-0">
        <div ref={scrollRef} className="flex-1 px-4 overflow-y-auto">
          <div className="space-y-4 py-4">
            {messages.length === 0 && (
              <div className="text-center text-muted-foreground py-8">
                <Sparkles className="h-12 w-12 mx-auto mb-3 opacity-50" />
                <p className="text-sm">输入您要搜索的数据集描述</p>
                <p className="text-xs mt-1">例如：&quot;半导体行业的高质量传感器数据&quot;</p>
              </div>
            )}

            {messages.map((message) => (
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

                {message.role === "assistant" && currentForm?.form_id && message.a2ui_form?.form_id === currentForm.form_id && (
                  <div className="w-full max-w-[90%]">
                    <A2UIForm
                      schema={message.a2ui_form}
                      sessionId={sessionId}
                      onSubmit={handleFormSubmit}
                      onCancel={handleFormCancel}
                    />
                  </div>
                )}

                {message.datasets && message.datasets.length > 0 && (
                  <div className="w-full max-w-[90%] space-y-2 mt-2">
                    <p className="text-xs text-muted-foreground">
                      找到 {message.datasets.length} 个数据集
                    </p>
                    <div className="grid gap-2">
                      {message.datasets.map((dataset) => (
                        <button
                          key={dataset.id}
                          onClick={() => handleDatasetClick(dataset)}
                          className="text-left p-3 rounded-lg border hover:bg-accent transition-colors"
                        >
                          <div className="font-medium text-sm">{dataset.name}</div>
                          {dataset.description && (
                            <p className="text-xs text-muted-foreground line-clamp-2 mt-1">
                              {dataset.description}
                            </p>
                          )}
                          <div className="flex gap-2 mt-2">
                            {dataset.tags?.slice(0, 3).map((tag) => (
                              <span
                                key={tag}
                                className="text-xs px-2 py-0.5 rounded-full bg-secondary"
                              >
                                {tag}
                              </span>
                            ))}
                          </div>
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))}

            {isLoading && (
              <div className="flex items-center gap-2 text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin" />
                <span className="text-sm">处理中...</span>
              </div>
            )}
          </div>
        </div>

        <div className="border-t p-4">
          <form onSubmit={handleSubmit} className="flex gap-2">
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="描述您需要的数据集..."
              disabled={isLoading || !!currentForm}
              className="flex-1"
            />
            <Button type="submit" disabled={isLoading || !input.trim() || !!currentForm}>
              <Send className="h-4 w-4" />
            </Button>
          </form>
          {currentForm && (
            <p className="text-xs text-muted-foreground mt-2 text-center">
              请先填写上方表单以继续搜索
            </p>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
