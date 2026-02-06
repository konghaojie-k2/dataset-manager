import { v4 as uuidv4 } from "uuid";
import { ReactNode, useEffect, useRef } from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { useStreamContext } from "@/providers/Stream";
import { useState, FormEvent } from "react";
import { Button } from "../ui/button";
import { Checkpoint, Message } from "@langchain/langgraph-sdk";
import { AssistantMessage, AssistantMessageLoading } from "./messages/ai";
import { HumanMessage } from "./messages/human";
import {
  DO_NOT_RENDER_ID_PREFIX,
  ensureToolCallsHaveResponses,
} from "@/lib/ensure-tool-responses";
import { SupermarketLogo } from "../icons/SupermarketLogos";
import { TooltipIconButton } from "./tooltip-icon-button";
import {
  ArrowDown,
  LoaderCircle,
  PanelRightOpen,
  PanelRightClose,
  SquarePen,
  XIcon,
  Plus,
  ChevronDown,
} from "lucide-react";
import { useQueryState, parseAsBoolean } from "nuqs";
import { StickToBottom, useStickToBottomContext } from "use-stick-to-bottom";
import ThreadHistory from "./history";
import { toast } from "sonner";
import { useMediaQuery } from "@/hooks/useMediaQuery";
import { Label } from "../ui/label";
import { Switch } from "../ui/switch";
import { GitHubSVG } from "../icons/github";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "../ui/tooltip";
import { useFileUpload } from "@/hooks/use-file-upload";
import { ContentBlocksPreview } from "./ContentBlocksPreview";
import {
  useArtifactOpen,
  ArtifactContent,
  ArtifactTitle,
  useArtifactContext,
} from "./artifact";
import { type Dataset } from "@/lib/api-extension";

function StickyToBottomContent(props: {
  content: ReactNode;
  footer?: ReactNode;
  className?: string;
  contentClassName?: string;
}) {
  const context = useStickToBottomContext();
  const isChatStarted = props.contentClassName?.includes("justify-center") ?? false;
  return (
    <div className="flex flex-col h-full w-full overflow-hidden">
      <div
        ref={context.scrollRef}
        className={cn("flex-1", props.className)}
      >
        <div
          ref={context.contentRef}
          className={cn(props.contentClassName, isChatStarted && "flex-1")}
        >
          {props.content}
        </div>
      </div>

      <div className="shrink-0">
        {props.footer}
      </div>
    </div>
  );
}

function ScrollToBottom(props: { className?: string }) {
  const { isAtBottom, scrollToBottom } = useStickToBottomContext();

  if (isAtBottom) return null;
  return (
    <Button
      variant="outline"
      className={props.className}
      onClick={() => scrollToBottom()}
    >
      <ArrowDown className="h-4 w-4" />
      <span>Scroll to bottom</span>
    </Button>
  );
}

export interface ThreadProps {
  selectedDataset?: Dataset | null;
  onDatasetSelect?: (dataset: Dataset) => void;
  datasets?: Dataset[];
}

export function Thread({
  selectedDataset,
  onDatasetSelect,
  datasets = []
}: ThreadProps) {
  const [threadId, setThreadId] = useQueryState("threadId");
  const isLargeScreen = useMediaQuery("(min-width: 1024px)");
  const [chatHistoryOpen, setChatHistoryOpen] = useQueryState(
    "chatHistoryOpen",
    parseAsBoolean.withDefault(false),
  );

  const {
    isLoading,
    messages,
    stream,
    contentBlocks,
    removeBlock,
    submit,
  } = useStreamContext();

  // Local state for input management
  const [input, setInput] = useState("");

  const {
    handleFileUpload: originalHandleFileUpload,
    dragOver,
    dropRef,
  } = useFileUpload();

  // Create a wrapper for file upload to match the expected signature
  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      // Create a DataTransfer object to simulate a drop event or call the internal logic if exposed
      // Since useFileUpload doesn't expose a direct method for file input, we'll try to adapt
      // This part might need adjustment based on the actual implementation of useFileUpload
      console.log("File selected:", e.target.files[0]);
      // For now, let's just log. In a real implementation, we would need to pass these files to the stream context
    }
  };

  const handlePaste = (e: React.ClipboardEvent) => {
    // Implement paste logic if needed
  };

  const [hideToolCalls, setHideToolCalls] = useQueryState(
    "hideToolCalls",
    parseAsBoolean.withDefault(false),
  );

  const { artifactOpen, closeArtifact } = useArtifactContext();

  // When a dataset is selected, start a new thread with context
  useEffect(() => {
    if (selectedDataset) {
      // Logic to start new thread with dataset context would go here
      // For now, we'll just log
      console.log("Starting chat with dataset:", selectedDataset.name);
    }
  }, [selectedDataset]);

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    
    const trimmedInput = input?.trim();
    
    // If we have input and submit method, submit the message
    if (submit && trimmedInput) {
      const newMessage: Message = { type: "human", content: trimmedInput };
      submit(
        { messages: [newMessage] },
        {
          streamMode: ["values"],
          streamSubgraphs: true,
          streamResumable: true,
        },
      );
      
      // Clear input after submission
      setInput("");
    } else if (!submit) {
      console.warn("submit method not available");
    } else if (!trimmedInput) {
      console.warn("No input to submit");
    }
  }

  const handleRegenerate = async (
    parentCheckpoint: Checkpoint | null | undefined,
  ) => {
    if (!parentCheckpoint && messages) {
      // Regenerate the last user message
      const lastUserMessageIndex = messages.findLastIndex(
        (m) => m.type === "human",
      );
      if (lastUserMessageIndex !== -1) {
        const lastUserMessage = messages[lastUserMessageIndex];
        const messagesToResend = messages.slice(0, lastUserMessageIndex);
        // We'd need a way to restart the stream with these messages
        // For now, this is a placeholder
      }
    }
  };

  const chatStarted = (messages?.length ?? 0) > 0;
  
  // Check if we haven't received the first token yet
  const firstTokenReceived = (messages?.length ?? 0) > 0;

  const hasNoAIOrToolMessages = !messages?.find(
    (m) => m.type === "ai" || m.type === "tool",
  );

  return (
    <div className="flex h-full w-full overflow-hidden">
      <div className="relative hidden lg:flex">
        <motion.div
          className="absolute z-20 h-full overflow-hidden border-r bg-white"
          style={{ width: 300 }}
          animate={
            isLargeScreen
              ? { x: chatHistoryOpen ? 0 : -300 }
              : { x: chatHistoryOpen ? 0 : -300 }
          }
          initial={{ x: -300 }}
          transition={
            isLargeScreen
              ? { type: "spring", stiffness: 300, damping: 30 }
              : { duration: 0 }
          }
        >
          <div
            className="relative h-full"
            style={{ width: 300 }}
          >
            <ThreadHistory />
          </div>
        </motion.div>
      </div>

      <div
        className={cn(
          "grid w-full grid-cols-[1fr_0fr] transition-all duration-500",
          artifactOpen && "grid-cols-[3fr_2fr]",
        )}
      >
        <motion.div
          className={cn(
            "relative flex min-w-0 flex-1 flex-col overflow-hidden",
            !chatStarted && "grid-rows-[1fr]",
          )}
          layout={isLargeScreen}
          animate={{
            marginLeft: chatHistoryOpen ? (isLargeScreen ? 300 : 0) : 0,
            width: chatHistoryOpen
              ? isLargeScreen
                ? "calc(100% - 300px)"
                : "100%"
              : "100%",
          }}
          transition={
            isLargeScreen
              ? { type: "spring", stiffness: 300, damping: 30 }
              : { duration: 0 }
          }
        >
          {!chatStarted && (
            <div className="absolute top-0 left-0 z-10 flex w-full items-center justify-between gap-3 p-2 pl-4">
              <div>
                {(!chatHistoryOpen || !isLargeScreen) && (
                  <Button
                    className="hover:bg-gray-100"
                    variant="ghost"
                    onClick={() => setChatHistoryOpen((p) => !p)}
                  >
                    {chatHistoryOpen ? (
                      <PanelRightOpen className="size-5" />
                    ) : (
                      <PanelRightClose className="size-5" />
                    )}
                  </Button>
                )}
              </div>
            </div>
          )}
          {chatStarted && (
            <>
              {/* Header */}
              <div className="relative z-10 flex items-center justify-between gap-3 p-2">
                <div className="relative flex items-center justify-start gap-2">
                  <div className="absolute left-0 z-10">
                    {(!chatHistoryOpen || !isLargeScreen) && (
                      <Button
                        className="hover:bg-gray-100"
                        variant="ghost"
                        onClick={() => setChatHistoryOpen((p) => !p)}
                      >
                        {chatHistoryOpen ? (
                          <PanelRightOpen className="size-5" />
                        ) : (
                          <PanelRightClose className="size-5" />
                        )}
                      </Button>
                    )}
                  </div>
                  <motion.button
                    className="flex cursor-pointer items-center gap-2"
                    onClick={() => setThreadId(null)}
                    animate={{
                      marginLeft: !chatHistoryOpen ? 48 : 0,
                    }}
                    transition={{
                      type: "spring",
                      stiffness: 300,
                      damping: 30,
                    }}
                  >
                    <SupermarketLogo
                      type="dataset"
                      width={32}
                      height={32}
                    />
                    <span className="text-xl font-semibold tracking-tight">
                      数据集助手
                    </span>
                  </motion.button>
                </div>

                <div className="flex items-center gap-4">
                  <TooltipIconButton
                    size="lg"
                    className="p-4"
                    tooltip="New thread"
                    variant="ghost"
                    onClick={() => setThreadId(null)}
                  >
                    <SquarePen className="size-5" />
                  </TooltipIconButton>
                </div>

                <div className="from-background to-background/0 absolute inset-x-0 top-full h-5 bg-gradient-to-b" />
              </div>
            </>
          )}

          <StickToBottom className="relative flex-1 overflow-hidden">
            <StickyToBottomContent
              className={cn(
                "overflow-y-scroll px-4 bg-[#faf8f5] [&::-webkit-scrollbar]:w-1.5 [&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-thumb]:bg-gray-300 [&::-webkit-scrollbar-track]:transparent",
              )}
              contentClassName={cn(
                "pt-8 pb-8 max-w-3xl mx-auto flex flex-col gap-4 w-full",
                !chatStarted && "flex-1 flex flex-col justify-center items-center pt-0 pb-0",
              )}
              content={
                <>
                  {!chatStarted && (
                    <div className="flex flex-col items-center justify-center text-center px-4 py-12">
                      <div className="mb-6">
                        <SupermarketLogo type="dataset" className="h-16 w-16 mx-auto mb-4" />
                        <h2 className="text-3xl font-bold text-[#1a1a1a] mb-2" style={{ fontFamily: 'var(--font-playfair)' }}>
                          数据集助手
                        </h2>
                        <p className="text-gray-600 text-base max-w-md mx-auto">
                          我可以帮您搜索、浏览和分析数据集。您可以问我关于数据集的问题，或者让我帮您找到特定的数据集。
                        </p>
                      </div>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-w-2xl w-full mt-6">
                        <button
                          onClick={() => setInput("有哪些数据集？")}
                          className="text-left p-4 bg-white rounded-lg border border-gray-200 hover:border-[#c75b39] hover:shadow-md transition-all text-sm text-gray-700 hover:text-[#1a1a1a]"
                        >
                          <div className="font-medium mb-1">有哪些数据集？</div>
                          <div className="text-xs text-gray-500">查看所有可用的数据集</div>
                        </button>
                        <button
                          onClick={() => setInput("搜索有色金属相关的数据集")}
                          className="text-left p-4 bg-white rounded-lg border border-gray-200 hover:border-[#c75b39] hover:shadow-md transition-all text-sm text-gray-700 hover:text-[#1a1a1a]"
                        >
                          <div className="font-medium mb-1">搜索数据集</div>
                          <div className="text-xs text-gray-500">按行业、标签或关键词搜索</div>
                        </button>
                        <button
                          onClick={() => setInput("帮我分析一下数据集的质量")}
                          className="text-left p-4 bg-white rounded-lg border border-gray-200 hover:border-[#c75b39] hover:shadow-md transition-all text-sm text-gray-700 hover:text-[#1a1a1a]"
                        >
                          <div className="font-medium mb-1">数据分析</div>
                          <div className="text-xs text-gray-500">获取数据集的详细分析</div>
                        </button>
                        <button
                          onClick={() => setInput("显示数据集预览")}
                          className="text-left p-4 bg-white rounded-lg border border-gray-200 hover:border-[#c75b39] hover:shadow-md transition-all text-sm text-gray-700 hover:text-[#1a1a1a]"
                        >
                          <div className="font-medium mb-1">预览数据</div>
                          <div className="text-xs text-gray-500">查看数据集的前几行数据</div>
                        </button>
                      </div>
                    </div>
                  )}
                  {(messages || [])
                    .filter((m) => !m.id?.startsWith(DO_NOT_RENDER_ID_PREFIX))
                    .map((message, index) =>
                      message.type === "human" ? (
                        <HumanMessage
                          key={message.id || `${message.type}-${index}`}
                          message={message}
                          isLoading={isLoading}
                        />
                      ) : (
                        <AssistantMessage
                          key={message.id || `${message.type}-${index}`}
                          message={message}
                          isLoading={isLoading}
                          handleRegenerate={handleRegenerate}
                        />
                      ),
                    )}
                  {/* Special rendering case where there are no AI/tool messages, but there is an interrupt.
                    We need to render it outside of the messages list, since there are no messages to render */}
                  {hasNoAIOrToolMessages && !!stream?.interrupt && (
                    <AssistantMessage
                      key="interrupt-msg"
                      message={undefined}
                      isLoading={isLoading}
                      handleRegenerate={handleRegenerate}
                    />
                  )}
                  {isLoading && !firstTokenReceived && (
                    <AssistantMessageLoading />
                  )}
                </>
              }
              footer={
                <div className="flex flex-col items-center gap-4 bg-[#faf8f5] pb-8 w-full px-4">
                  <div className="relative w-full max-w-3xl">
                    <ScrollToBottom className="animate-in fade-in-0 zoom-in-95 absolute bottom-full left-1/2 mb-4 -translate-x-1/2" />
                    
                    <div
                      ref={dropRef}
                      className={cn(
                        "bg-white relative z-10 mx-auto w-full rounded-2xl shadow-sm transition-all border border-gray-200",
                        dragOver
                          ? "border-primary border-2 border-dotted"
                          : "border-gray-200",
                      )}
                    >
                    <form
                      onSubmit={handleSubmit}
                      className="mx-auto grid max-w-3xl grid-rows-[1fr_auto] gap-2"
                    >
                      <ContentBlocksPreview
                        blocks={contentBlocks || []}
                        onRemove={removeBlock}
                      />
                      <textarea
                        value={input || ""}
                        onChange={(e) => {
                          setInput(e.target.value);
                        }}
                        onPaste={handlePaste}
                        onKeyDown={(e) => {
                          if (
                            e.key === "Enter" &&
                            !e.shiftKey &&
                            !e.metaKey &&
                            !e.nativeEvent.isComposing
                          ) {
                            e.preventDefault();
                            const el = e.target as HTMLElement | undefined;
                            const form = el?.closest("form");
                            form?.requestSubmit();
                          }
                        }}
                        placeholder="Type your message..."
                        className="field-sizing-content resize-none border-none bg-transparent p-3.5 pb-0 shadow-none ring-0 outline-none focus:ring-0 focus:outline-none text-gray-900 placeholder:text-gray-500"
                      />

                      <div className="flex items-center gap-6 p-2 pt-4">
                        <div>
                          <div className="flex items-center space-x-2">
                            <Switch
                              id="render-tool-calls"
                              checked={hideToolCalls ?? false}
                              onCheckedChange={setHideToolCalls}
                            />
                            <Label
                              htmlFor="render-tool-calls"
                              className="text-sm text-gray-800"
                            >
                              Hide Tool Calls
                            </Label>
                          </div>
                        </div>
                        <Label
                          htmlFor="file-input"
                          className="flex cursor-pointer items-center gap-2 hover:text-gray-900 transition-colors"
                        >
                          <Plus className="size-5 text-gray-700" />
                          <span className="text-sm text-gray-700">
                            Upload PDF or Image
                          </span>
                        </Label>
                        <input
                          id="file-input"
                          type="file"
                          onChange={handleFileUpload}
                          multiple
                          accept="image/jpeg,image/png,image/gif,image/webp,application/pdf"
                          className="hidden"
                        />
                        {stream?.isLoading ? (
                          <Button
                            key="stop"
                            onClick={() => stream?.stop()}
                            className="ml-auto"
                          >
                            <LoaderCircle className="h-4 w-4 animate-spin" />
                            Cancel
                          </Button>
                        ) : (
                          <Button
                            type="submit"
                            className="ml-auto shadow-md transition-all"
                            disabled={
                              isLoading ||
                              (!input?.trim() && (!contentBlocks || contentBlocks.length === 0))
                            }
                          >
                            Send
                          </Button>
                        )}
                      </div>
                    </form>
                    </div>
                  </div>
                </div>
              }
            />
          </StickToBottom>
        </motion.div>
        <div className="relative flex flex-col border-l">
          <div className="absolute inset-0 flex min-w-[30vw] flex-col">
            <div className="grid grid-cols-[1fr_auto] border-b p-4">
              <ArtifactTitle className="truncate overflow-hidden" />
              <button
                onClick={closeArtifact}
                className="cursor-pointer"
              >
                <XIcon className="size-5" />
              </button>
            </div>
            <ArtifactContent className="relative flex-grow" />
          </div>
        </div>
      </div>
    </div>
  );
}
