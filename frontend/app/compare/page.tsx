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
  { url: "https://library.municode.com/CA/California_City/codes/Code_of_Ordinances?nodeId=COOR_TIT8BURE_CH12SMRESOENSYPE_S8-12.03AP", label: "Building Code 2024" },
  { url: "https://library.municode.com/CA/California_City/codes/Code_of_Ordinances?nodeId=COOR_TIT8BURE_CH12SMRESOENSYPE_S8-12.02DE2", label: "Safety Guidelines" },
  { url: "https://library.municode.com/CA/California_City/codes/Code_of_Ordinances?nodeId=COOR_TIT9LAUSDE_CH2ZO_ART6RMIREDIMEWDE_S9-2.601PEUS", label: "Permit Requirements" },
  { url: "https://library.municode.com/CA/California_City/codes/Code_of_Ordinances?nodeId=COOR_TIT8BURE_CH5SWPOPOCADI_S8-5.04COST", label: "Construction Standards" },
  { url: "https://library.municode.com/CA/California_City/codes/Code_of_Ordinances?nodeId=COOR_TIT9LAUSDE_CH3LADI_ART4RE_S9-3.403DEPAREPU", label: "Zoning Laws" },
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
  // State for the left panel
  const [leftSelectedState, setLeftSelectedState] = useState("California");
  const [leftSelectedCity, setLeftSelectedCity] = useState("Los Angeles");
  const [leftMessages, setLeftMessages] = useState<Message[]>([]);

  // State for the right panel
  const [rightSelectedState, setRightSelectedState] = useState("California");
  const [rightSelectedCity, setRightSelectedCity] = useState("Los Angeles");
  const messagesRef = useRef<HTMLDivElement>(null);
  const formRef = useRef<HTMLFormElement>(null);

  useEffect(() => {
    if (messagesRef.current) {
      messagesRef.current.scrollTop = messagesRef.current.scrollHeight;
    }
  }, [messages]);

  // Handlers for the left panel
  const handleLeftStateChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const state = e.target.value;
    setLeftSelectedState(state);
    setLeftSelectedCity(cities[state] ? cities[state][0] : "");
  };

  const handleLeftCityChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setLeftSelectedCity(e.target.value);
  };


  // Handlers for the right panel
  const handleRightStateChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const state = e.target.value;
    setRightSelectedState(state);
    setRightSelectedCity(cities[state] ? cities[state][0] : "");
  };

  const handleRightCityChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setRightSelectedCity(e.target.value);
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
      console.log("print meeeee")
      // Stream response from the backend on port 8000
      const response = await fetch("http://localhost:8000/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: input }),
      });

      if (!response.body) throw new Error("No response body");
      console.log("responseeee",response.body)
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
          <div className="flex-grow flex w-full">
            {/* Left Side Chat Messages */}
            <div className="flex-1 p-4 overflow-hidden">
              <div className="flex gap-4 mb-4">
                {/* State Dropdown */}
                <select
                    value={leftSelectedState}
                    onChange={handleLeftStateChange}
                    className="block w-[180px] border border-gray-300 rounded-md py-2 px-3 focus:outline-none focus:ring-1 focus:ring-blue-500"
                >
                  {states.map((state) => (
                      <option key={state} value={state}>
                        {state}
                      </option>
                  ))}
                </select>

                {/* City Dropdown */}
                <select
                    value={leftSelectedCity}
                    onChange={handleLeftCityChange}
                    className="block w-[180px] border border-gray-300 rounded-md py-2 px-3 focus:outline-none focus:ring-1 focus:ring-blue-500"
                >
                  {cities[leftSelectedState]?.map((city) => (
                      <option key={city} value={city}>
                        {city}
                      </option>
                  ))}
                </select>
              </div>

              <ChatMessageList ref={messagesRef} className="h-full overflow-y-auto">
                {messages.map((message, index) => (
                    <ChatBubble
                        key={index}
                        variant={message.role === "user" ? "sent" : "received"}
                    >
                      <ChatBubbleAvatar src="" fallback={message.role === "user" ? "👨🏽" : "🤖"} />
                      <ChatBubbleMessage>
                        {message.content.split("```").map((part, partIndex) => {
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
            </div>

            {/* Divider */}
            <div className="w-0.5 bg-black"></div>

            {/* Right Side Chat Messages (Duplicate View) */}
            <div className="flex-1 p-4 overflow-hidden">
              <div className="flex gap-4 mb-4">
                {/* State Dropdown */}
                <select
                    value={rightSelectedState}
                    onChange={handleRightStateChange}
                    className="block w-[180px] border border-gray-300 rounded-md py-2 px-3 focus:outline-none focus:ring-1 focus:ring-blue-500"
                >
                  {states.map((state) => (
                      <option key={state} value={state}>
                        {state}
                      </option>
                  ))}
                </select>

                {/* City Dropdown */}
                <select
                    value={rightSelectedCity}
                    onChange={handleRightCityChange}
                    className="block w-[180px] border border-gray-300 rounded-md py-2 px-3 focus:outline-none focus:ring-1 focus:ring-blue-500"
                >
                  {cities[rightSelectedState]?.map((city) => (
                      <option key={city} value={city}>
                        {city}
                      </option>
                  ))}
                </select>
              </div>

              <ChatMessageList ref={messagesRef} className="h-full overflow-y-auto">
                {messages.map((message, index) => (
                    <ChatBubble
                        key={`duplicate-${index}`}
                        variant={message.role === "user" ? "sent" : "received"}
                    >
                      <ChatBubbleAvatar src="" fallback={message.role === "user" ? "👨🏽" : "🤖"} />
                      <ChatBubbleMessage>
                        {message.content.split("```").map((part, partIndex) => {
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
            </div>
          </div>

          {/* Main Chat Input */}
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
