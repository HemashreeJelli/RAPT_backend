import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from "jsr:@supabase/supabase-js@2"

// 🔥 Native AI session
const model = new Supabase.ai.Session("gte-small")

serve(async (req) => {
  try {
    const { job_id, description } = await req.json()

    if (!job_id || !description) {
      return new Response("Missing fields", { status: 400 })
    }

    // 🧠 Generate embedding
    const result = await model.run(description, {
      mean_pool: true,
      normalize: true,
    })

    // ⭐ IMPORTANT FIX
    const embedding = Array.from(result)

    // 🔐 Service role client
    const supabase = createClient(
      Deno.env.get("SUPABASE_URL")!,
      Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!
    )

    const { error } = await supabase
      .from("jobs")
      .update({ embedding })
      .eq("id", job_id)

    if (error) throw error

    return new Response(JSON.stringify({ success: true }), {
      headers: { "Content-Type": "application/json" },
    })

  } catch (err) {
    console.error(err)
    return new Response(
      JSON.stringify({ error: err.message }),
      { status: 500 }
    )
  }
})