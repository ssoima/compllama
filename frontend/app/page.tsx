"use client";

import {
  ChatBubble,
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
  Pin,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import CodeDisplayBlock from "@/components/code-display-block";
import Navbar from "@/components/ui/navbar";

const SAMPLE_SOURCES = [
  { url: "https://example.com/doc1", label: "Building Code 2024" },
  { url: "https://example.com/doc2", label: "Safety Guidelines" },
  { url: "https://example.com/doc3", label: "Permit Requirements" },
  { url: "https://example.com/doc4", label: "Construction Standards" },
  { url: "https://example.com/doc5", label: "Zoning Laws" },
];

type Message = {
  id: string; // Unique ID for each message
  role: "user" | "assistant"; // Specifies who sent the message
  content: string; // The actual text of the message
  timestamp?: Date; // Optional timestamp for when the message was sent
};

const states = ["California", "Texas", "Florida", "Illinois", "Pennsylvania", "Ohio", "Georgia", "Michigan", "Virginia"];

const cities = {
  California: ["Los Angeles", "San Francisco", "San Diego", "San Jose", "Sacramento"],
  Texas: ["Houston", "Dallas", "Austin", "San Antonio", "Fort Worth"],
  Florida: ["Miami", "Orlando", "Tampa", "Jacksonville", "Tallahassee"],
  Illinois: ["Chicago", "Aurora", "Naperville", "Joliet", "Rockford"],
  Pennsylvania: ["Philadelphia", "Pittsburgh", "Allentown", "Erie", "Reading"],
  Ohio: ["Columbus", "Cleveland", "Cincinnati", "Toledo", "Akron"],
  Georgia: ["Atlanta", "Augusta", "Savannah", "Athens", "Macon"],
  Michigan: ["Detroit", "Grand Rapids", "Warren", "Sterling Heights", "Ann Arbor"],
  Virginia: ["Virginia Beach", "Norfolk", "Chesapeake", "Richmond", "Newport News"]
};



export default function Home() {
  const [isGenerating, setIsGenerating] = useState(false);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [selectedState, setSelectedState] = useState("California"); // Default state
  const [selectedCity, setSelectedCity] = useState("Los Angeles"); // Default city
  const messagesRef = useRef<HTMLDivElement>(null);
  const formRef = useRef<HTMLFormElement>(null);

  useEffect(() => {
    if (messagesRef.current) {
      messagesRef.current.scrollTop = messagesRef.current.scrollHeight;
    }
  }, [messages]);

  const handleStateChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const state = e.target.value;
    setSelectedState(state);

    // Set the first city only if cities[state] is defined
    if (cities[state]) {
      setSelectedCity(cities[state][0]);
    } else {
      setSelectedCity("");
    }
  };
  const handleCityChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedCity(e.target.value);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
  };

  const handleSourceClick = (url: string) => {
    window.open(url, "_blank"); // Open link in a new tab
  };

  const getRandomSources = () => {
    const numberOfSources = Math.floor(Math.random() * 3) + 1; // Random number between 1-3
    const shuffled = [...SAMPLE_SOURCES].sort(() => 0.5 - Math.random());
    return shuffled.slice(0, numberOfSources);
  };

  const requestChatCompletion = async () => {
    // Initialize an empty assistant message to render streaming response
    const assistantMessage: {
      role: string;
      sources: ({ label: string; url: string })[];
      id: string;
      content: string;
      timestamp: Date
    } = {
      id: String(Date.now() + 1),
      role: "assistant",
      content: "",
      timestamp: new Date(),
      sources: getRandomSources(), // Add this line
    };


    try {
      // Stream response from the backend on port 8000
      const response = await fetch("http://localhost:8000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: input }),
      });

      if (!response.body) throw new Error("No response body");

      // ReadableStream to handle streaming response
      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");

      let newContent = "";
      setMessages((prevMessages) => [...prevMessages, assistantMessage]);

      // Process each chunk from the response
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        // Decode and parse each chunk of the streamed response
        const chunk = decoder.decode(value, { stream: true });
        try {
          // Split and parse individual JSON messages from the chunk
          const lines = chunk.split("\n").filter(line => line.trim() !== "");
          lines.forEach(line => {
            const parsed = JSON.parse(line);
            if (parsed.content) {
              if (parsed.content !== "Assistant> ") {
                newContent += parsed.content;
              }

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
          });
        } catch (err) {
          assistantMessage.content = "An error occurred while processing the response.";
          setMessages((prevMessages) => [...prevMessages, assistantMessage]);

          console.error("Failed to parse JSON chunk:", err);
        }
      }
    } catch (error) {
      console.error("Error during streaming:", error);
    } finally {
      setIsGenerating(false);
    }
  };

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
    await requestChatCompletion()
    setIsLoading(false);

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
    if (action === "Source") {
      // Replace this URL with the source link you want to redirect to
      const sourceUrl = "https://example.com/source-url";
      window.open(sourceUrl, "_blank"); // Open link in a new tab
    }
  };

  return (
      <div className="flex">
      <Navbar />

      <main className="flex h-screen w-full max-w-3xl flex-col items-center mx-auto py-6">

        <div className="flex gap-4 mb-4">
          {/* State Dropdown */}
          <div className="relative">
            <select
                value={selectedState}
                onChange={handleStateChange}
                className="block w-[180px] border border-gray-300 rounded-md py-2 px-3 focus:outline-none focus:ring-1 focus:ring-blue-500"
            >
              {states.map((state) => (
                  <option key={state} value={state}>
                    {state}
                  </option>
              ))}
            </select>
          </div>

          {/* City Dropdown */}
          <div className="relative">
            <select
                value={selectedCity}
                onChange={handleCityChange}
                className="block w-[180px] border border-gray-300 rounded-md py-2 px-3 focus:outline-none focus:ring-1 focus:ring-blue-500"
            >
              {/* Check if cities[selectedState] exists before mapping */}
              {cities[selectedState]?.map((city) => (
                  <option key={city} value={city}>
                    {city}
                  </option>
              ))}
            </select>
          </div>
        </div>
      <ChatMessageList ref={messagesRef}>
        {messages.length === 0 && (
          <div className="w-full bg-background shadow-sm border rounded-lg p-8 flex flex-col gap-2">
            <h1 className="font-bold">Welcome to the CompLlama</h1>
            <p className="text-muted-foreground text-sm">
              A compliance app for construction companies expanding across California that instantly confirms if projects meet local building codes and highlights differences across city regulations, allowing quick adaptation to unique requirements in each area.
            </p>
          </div>
        )}

        {messages.map((message, index) => (
          <ChatBubble
            key={index}
            variant={message.role == "user" ? "sent" : "received"}
          >
            <ChatBubbleAvatar
              src=""
              fallback={message.role == "user" ? "👨🏽" : "🤖"}
            />
            <ChatBubbleMessage>
              {message.content.split("```").map((part: string, partIndex: number) => {
                if (partIndex % 2 === 0) {
                  return (
                    <Markdown key={partIndex} remarkPlugins={[remarkGfm]}>
                      {part}
                    </Markdown>
                  );
                } else {
                  return (
                    <pre className="whitespace-pre-wrap pt-2" key={partIndex}>
                      <CodeDisplayBlock code={part} lang="" />
                    </pre>
                  );
                }
              })}

            {message.role === "assistant" && (
              <div className="mt-2 flex flex-col gap-1">
                {!isGenerating && message.sources?.map((source, sourceIndex) => (
                  <div key={sourceIndex} className="flex items-center gap-2">
                    <Pin style={{ width: "16px", height: "16px" }} /> {/* Pin icon */}
                    <a
                      href={source.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-500 underline"
                    >
                      {source.label}
                    </a>
                  </div>
                ))}
              </div>
            )}
            </ChatBubbleMessage>
          </ChatBubble>
        ))}

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
      </div>
  );
}
