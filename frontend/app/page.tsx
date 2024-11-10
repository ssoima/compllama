"use client";

import {
  ChatBubble,
  ChatBubbleAction,
  ChatBubbleAvatar,
  ChatBubbleMessage,
} from "@/components/ui/chat/chat-bubble";
import { ChatInput } from "@/components/ui/chat/chat-input";
import { ChatMessageList } from "@/components/ui/chat/chat-message-list";
import { Button } from "@/components/ui/button";
import {
  CopyIcon,
  CornerDownLeft,
  Mic,
  Paperclip,
  RefreshCcw,
  Volume2,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import CodeDisplayBlock from "@/components/code-display-block";

const ChatAiIcons = [
  {
    icon: CopyIcon,
    label: "Copy",
  },
  {
    icon: RefreshCcw,
    label: "Refresh",
  },
  {
    icon: Volume2,
    label: "Volume",
  },
];

type Message = {
  id: string; // Unique ID for each message
  role: "user" | "assistant"; // Specifies who sent the message
  content: string; // The actual text of the message
  timestamp?: Date; // Optional timestamp for when the message was sent
};

export default function Home() {
  const [isGenerating, setIsGenerating] = useState(false);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const messagesRef = useRef<HTMLDivElement>(null);
  const formRef = useRef<HTMLFormElement>(null);

  useEffect(() => {
    if (messagesRef.current) {
      messagesRef.current.scrollTop = messagesRef.current.scrollHeight;
    }
  }, [messages]);

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
  };

  const requestChatCompletion = async () => {
    // Initialize an empty assistant message to render streaming response
    const assistantMessage: Message = {
      id: String(Date.now() + 1),
      role: "assistant",
      content: "",
      timestamp: new Date(),
    };
    setMessages((prevMessages) => [...prevMessages, assistantMessage]);
    try {
      // Stream response from the backend on port 3020
      const response = await fetch("http://localhost:8000/chat-stream", {
        method: "POST",
        mode: 'no-cors',
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: input }),
      });
      console.log("here I am")
      //if (!response.body) throw new Error("No response body");
      console.log("response.body: ",response.body)

      // ReadableStream to handle streaming response
      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");

      let newContent = "";

      // Process each chunk from the response
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        newContent += decoder.decode(value, { stream: true });

        // Update assistant message content incrementally
        setMessages((prevMessages) => {
          const updatedMessages = [...prevMessages];
          const lastMessageIndex = updatedMessages.length - 1;
          if (updatedMessages[lastMessageIndex].role === "assistant") {
            updatedMessages[lastMessageIndex] = {
              ...updatedMessages[lastMessageIndex],
              content: newContent,
            };
          }
          return updatedMessages;
        });
      }
    } catch (error) {
      console.error("Error during streaming:", error);
    } finally {
      setIsGenerating(false);
      setIsLoading(false);
    }
  }

  const onSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setIsGenerating(true);
    if (!input.trim()) return; // Ensure input is not empty

    // Create new user message
    const newMessage: Message = {
      id: String(Date.now()), // Unique ID (could use more sophisticated UUID if needed)
      role: "user",
      content: input,
      timestamp: new Date(),
    };

    // Add the new user message to messages
    setMessages((prevMessages) => [...prevMessages, newMessage]);
    setInput(""); // Clear the input field
    setIsLoading(true);
    setIsLoading(false);
    await requestChatCompletion()

  };

  const onKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (isGenerating || isLoading || !input) return;
      setIsGenerating(true);
      onSubmit(e as unknown as React.FormEvent<HTMLFormElement>);
    }
  };

  const handleActionClick = async (action: string, messageIndex: number) => {
    console.log("Action clicked:", action, "Message index:", messageIndex);
    if (action === "Refresh") {
      setIsGenerating(true);
      try {
        //await reload();
      } catch (error) {
        console.error("Error reloading:", error);
      } finally {
        setIsGenerating(false);
      }
    }

    if (action === "Copy") {
      const message = messages[messageIndex];
      if (message && message.role === "assistant") {
        navigator.clipboard.writeText(message.content);
      }
    }
  };

  return (
    <main className="flex h-screen w-full max-w-3xl flex-col items-center mx-auto py-6">
      <ChatMessageList ref={messagesRef}>
        {/* Initial Message */}
        {messages.length === 0 && (
          <div className="w-full bg-background shadow-sm border rounded-lg p-8 flex flex-col gap-2">
            <h1 className="font-bold">Welcome to the CompLlama</h1>
            <p className="text-muted-foreground text-sm">
              A compliance app for construction companies expanding across California that instantly confirms if projects meet local building codes and highlights differences across city regulations, allowing quick adaptation to unique requirements in each area.
            </p>
          </div>
        )}

        {/* Messages */}
        {messages &&
          messages.map((message, index) => (
            <ChatBubble
              key={index}
              variant={message.role == "user" ? "sent" : "received"}
            >
              <ChatBubbleAvatar
                src=""
                fallback={message.role == "user" ? "👨🏽" : "🤖"}
              />
              <ChatBubbleMessage
              >
                {message.content
                  .split("```")
                  .map((part: string, index: number) => {
                    if (index % 2 === 0) {
                      return (
                        <Markdown key={index} remarkPlugins={[remarkGfm]}>
                          {part}
                        </Markdown>
                      );
                    } else {
                      return (
                        <pre className="whitespace-pre-wrap pt-2" key={index}>
                          <CodeDisplayBlock code={part} lang="" />
                        </pre>
                      );
                    }
                  })}

                {message.role === "assistant" &&
                  messages.length - 1 === index && (
                    <div className="flex items-center mt-1.5 gap-1">
                      {!isGenerating && (
                        <>
                          {ChatAiIcons.map((icon, iconIndex) => {
                            const Icon = icon.icon;
                            return (
                              <ChatBubbleAction
                                variant="outline"
                                className="size-5"
                                key={iconIndex}
                                icon={<Icon className="size-3" />}
                                onClick={() =>
                                  handleActionClick(icon.label, index)
                                }
                              />
                            );
                          })}
                        </>
                      )}
                    </div>
                  )}
              </ChatBubbleMessage>
            </ChatBubble>
          ))}

        {/* Loading */}
        {isGenerating && (
          <ChatBubble variant="received">
            <ChatBubbleAvatar src="" fallback="🤖" />
            <ChatBubbleMessage isLoading />
          </ChatBubble>
        )}
      </ChatMessageList>
      <div className="w-full px-4">
        <form
          ref={formRef}
          onSubmit={onSubmit}
          className="relative rounded-lg border bg-background focus-within:ring-1 focus-within:ring-ring"
        >
          <ChatInput
            value={input}
            onKeyDown={onKeyDown}
            onChange={handleInputChange}
            placeholder="Type your message here..."
            className="min-h-12 resize-none rounded-lg bg-background border-0 p-3 shadow-none focus-visible:ring-0"
          />
          <div className="flex items-center p-3 pt-0">
            <Button variant="ghost" size="icon">
              <Paperclip className="size-4" />
              <span className="sr-only">Attach file</span>
            </Button>

            <Button variant="ghost" size="icon">
              <Mic className="size-4" />
              <span className="sr-only">Use Microphone</span>
            </Button>

            <Button
              disabled={!input || isLoading}
              type="submit"
              size="sm"
              className="ml-auto gap-1.5"
            >
              Send Message
              <CornerDownLeft className="size-3.5" />
            </Button>
          </div>
        </form>
      </div>
    </main>
  );
}
