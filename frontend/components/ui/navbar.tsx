import Link from "next/link";
import {BarChart, MessageSquare} from "lucide-react";

export default function Navbar() {
    return (
        <aside className="fixed inset-y-0 left-0 w-64 bg-white text-neutral-900 shadow-md border-r border-neutral-300">
            {/* Header */}
            <div className="flex items-center space-x-2 p-4 border-b border-neutral-300 bg-white">
                {/* Llama Icon */}
                <img
                    src="https://img.icons8.com/ios-filled/50/000000/llama.png"
                    alt="Llama Logo"
                    className="h-8 w-8"
                />
                <span className="text-lg font-semibold text-neutral-900">CompLlama</span>
            </div>

            {/* Navigation Links */}
            <nav className="flex flex-col p-4 space-y-2">
                <Link href="/" passHref>
                    <div
                        className="flex items-center px-4 py-2 rounded-lg text-sm font-medium transition-colors hover:bg-neutral-100">
                        <MessageSquare className="mr-3 h-4 w-4"/> Chat
                    </div>
                </Link>
                <Link href="/compare" passHref>
                    <div className="flex items-center px-4 py-2 rounded-lg text-sm font-medium transition-colors hover:bg-neutral-100">
                        <BarChart className="mr-3 h-4 w-4" /> Compare
                    </div>
                </Link>
            </nav>
        </aside>
    );
}
