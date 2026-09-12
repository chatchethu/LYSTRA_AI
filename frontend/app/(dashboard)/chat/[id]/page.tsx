import { ChatPage } from "@/components/chat/ChatPage";

export const metadata = {
  title: "Chat - LYSTRA AI",
  description: "Advanced Agentic Interface",
};

export default async function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <ChatPage conversationId={id} />;
}
