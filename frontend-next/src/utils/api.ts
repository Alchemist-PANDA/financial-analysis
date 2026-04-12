/**
 * REAL Fetch Guard implementation based on institutional stability requirements.
 * This prevents the "Unexpected token <" error by validating Content-Type 
 * before parsing JSON and handling Hugging Face sleeping states.
 */
export async function safeFetch(url: string, options: RequestInit = {}) {
  try {
    // Add default headers for JSON
    const headers = new Headers(options.headers || {});
    if (!headers.has('Content-Type')) {
      headers.set('Content-Type', 'application/json');
    }

    const res = await fetch(url, { ...options, headers });
    
    // Log for visibility in DevTools
    console.log(`[API REQUEST] URL: ${url}`);

    const contentType = res.headers.get("content-type") || "";
    const text = await res.text();

    // 🔴 Handle sleeping backend / HTML response
    if (!contentType.includes("application/json")) {
      console.error("[API_ERROR] Expected JSON, got HTML/Text. Response snippet:", text.slice(0, 200));
      
      if (text.includes('<!DOCTYPE') || text.includes('<html') || text.includes('Hugging Face')) {
        return {
          success: false,
          error: "Backend is waking up, please wait 20 seconds and refresh.",
          isHtml: true
        };
      }
      
      return {
        success: false,
        error: "Server returned non-JSON response.",
        status: res.status
      };
    }

    try {
      const data = JSON.parse(text);
      return {
        success: true,
        data: data
      };
    } catch {
      return {
        success: false,
        error: "Invalid JSON response from server"
      };
    }
  } catch (err: any) {
    console.error("[NETWORK_ERROR]", err);
    return {
      success: false,
      error: `Network error: ${err.message || 'Unknown failure'}`
    };
  }
}
