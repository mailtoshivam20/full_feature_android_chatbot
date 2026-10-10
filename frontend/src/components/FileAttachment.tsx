import { useRef, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import axios from "axios";
import client from "@/api/client";

interface Document {
  id: string;
  filename: string;
  content_type: string;
  size_bytes: number;
  is_indexed: boolean;
  created_at: string;
}

interface Props {
  chatId: string;
}

export default function FileAttachment({ chatId }: Props) {
  const [uploadProgress, setUploadProgress] = useState<number | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const queryClient = useQueryClient();

  const { data: docs } = useQuery({
    queryKey: ["files", chatId],
    queryFn: () => client.get<Document[]>(`/chats/${chatId}/files/`).then((r) => r.data),
    refetchInterval: (query) => {
      const hasUnindexed = query.state.data?.some((d) => !d.is_indexed);
      return hasUnindexed ? 2000 : false;
    },
  });

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    const token = sessionStorage.getItem("access_token");
    setUploadProgress(0);
    try {
      await axios.post(`/api/v1/chats/${chatId}/files/`, formData, {
        headers: { Authorization: `Bearer ${token}` },
        onUploadProgress: (ev) => {
          if (ev.total) setUploadProgress(Math.round((ev.loaded / ev.total) * 100));
        },
      });
      queryClient.invalidateQueries({ queryKey: ["files", chatId] });
    } catch (err: any) {
      alert(err?.response?.data?.detail || "Upload failed");
    } finally {
      setUploadProgress(null);
      if (inputRef.current) inputRef.current.value = "";
    }
  };

  const handleDelete = async (docId: string) => {
    await client.delete(`/api/v1/chats/${chatId}/files/${docId}`);
    queryClient.invalidateQueries({ queryKey: ["files", chatId] });
  };

  return (
    <div>
      <input
        ref={inputRef}
        type="file"
        className="hidden"
        accept=".pdf,.txt,.docx,.doc,.png,.jpg,.jpeg,.webp"
        onChange={handleFileChange}
      />
      <button
        onClick={() => inputRef.current?.click()}
        className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-500"
        title="Attach file"
      >
        📎
      </button>

      {uploadProgress !== null && (
        <div className="mt-1 text-xs text-gray-500">Uploading… {uploadProgress}%</div>
      )}

      {docs && docs.length > 0 && (
        <div className="mt-2 space-y-1">
          {docs.map((doc) => (
            <div
              key={doc.id}
              className="flex items-center gap-2 text-xs bg-gray-100 dark:bg-gray-800 rounded px-2 py-1"
            >
              <span className="truncate max-w-[160px]">{doc.filename}</span>
              {doc.is_indexed ? (
                <span className="text-green-500 shrink-0">✓</span>
              ) : (
                <span className="text-yellow-500 animate-pulse shrink-0">⏳</span>
              )}
              <button
                onClick={() => handleDelete(doc.id)}
                className="ml-auto text-red-400 hover:text-red-600 shrink-0"
              >
                ×
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
