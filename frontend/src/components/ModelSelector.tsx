import { useQuery } from "@tanstack/react-query";
import client from "@/api/client";
import { useChatStore } from "@/store/chatStore";

interface ModelInfo {
  id: string;
  display: string;
  context_tokens: number;
}

export default function ModelSelector() {
  const { selectedModel, setSelectedModel } = useChatStore();

  const { data: models } = useQuery({
    queryKey: ["models"],
    queryFn: () => client.get<ModelInfo[]>("/models").then((r) => r.data),
    staleTime: Infinity,
  });

  if (!models?.length) return null;

  return (
    <select
      value={selectedModel}
      onChange={(e) => setSelectedModel(e.target.value)}
      className="text-xs border border-gray-200 dark:border-gray-700 rounded-lg px-2 py-1 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
      aria-label="Select AI model"
    >
      {models.map((m) => (
        <option key={m.id} value={m.id}>
          {m.display}
        </option>
      ))}
    </select>
  );
}
