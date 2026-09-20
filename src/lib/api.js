export const API_BASE =
  import.meta.env.VITE_API_BASE ||
  "https://rcfb7kr4x0.execute-api.ap-south-1.amazonaws.com/prod";

async function post(path, body) {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok || data.error) {
    throw new Error(data.error || `Request failed (${res.status})`);
  }
  return data;
}

export async function getUploadUrl(fileType) {
  return post("/get-upload-url", { fileType });
}

export async function uploadToS3(uploadUrl, file, onProgress) {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("PUT", uploadUrl);
    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable) onProgress(Math.round((e.loaded / e.total) * 100));
    };
    xhr.onload = () => (xhr.status === 200 ? resolve() : reject(new Error("Upload failed")));
    xhr.onerror = () => reject(new Error("Upload failed"));
    xhr.send(file);
  });
}

export async function processNotice(fileKey, language) {
  return post("/process-notice", { fileKey, language });
}

export async function processText(text, language) {
  return post("/process-notice", { text, language });
}