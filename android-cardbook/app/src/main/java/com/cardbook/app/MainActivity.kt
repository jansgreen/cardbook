package com.cardbook.app

import android.app.Activity
import android.content.Context
import android.graphics.Color
import android.graphics.Typeface
import android.graphics.drawable.GradientDrawable
import android.os.Bundle
import android.text.InputType
import android.view.Gravity
import android.view.View
import android.widget.Button
import android.widget.EditText
import android.widget.HorizontalScrollView
import android.widget.LinearLayout
import android.widget.ProgressBar
import android.widget.ScrollView
import android.widget.TextView
import org.json.JSONArray
import org.json.JSONObject
import java.io.BufferedReader
import java.io.InputStreamReader
import java.io.OutputStreamWriter
import java.net.HttpURLConnection
import java.net.URL

private const val BLUE = 0xFF0057B8.toInt()
private const val BLUE_DARK = 0xFF003875.toInt()
private const val GOLD = 0xFFD8A441.toInt()
private const val INK = 0xFF10233F.toInt()
private const val MUTED = 0xFF637189.toInt()
private const val BG = 0xFFF4F6F9.toInt()
private const val WHITE = 0xFFFFFFFF.toInt()

class MainActivity : Activity() {
    private lateinit var session: SessionStore
    private lateinit var api: CardbookApi
    private lateinit var root: LinearLayout
    private lateinit var content: LinearLayout

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        session = SessionStore(this)
        api = CardbookApi(session)
        renderShell()
        if (session.accessToken.isNullOrBlank()) renderAuth() else renderDashboard("Resumen")
    }

    private fun renderShell() {
        root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setBackgroundColor(BG)
        }
        setContentView(root)
    }

    private fun clear() {
        root.removeAllViews()
    }

    private fun header(title: String, showLogout: Boolean = false) {
        val bar = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
            setPadding(dp(18), dp(14), dp(18), dp(14))
            background = gradient(BLUE_DARK, BLUE)
        }
        val brand = TextView(this).apply {
            text = title
            setTextColor(WHITE)
            textSize = 22f
            typeface = Typeface.DEFAULT_BOLD
            layoutParams = LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f)
        }
        bar.addView(brand)
        if (showLogout) {
            bar.addView(actionButton("Salir", WHITE, BLUE_DARK) {
                session.clear()
                renderAuth()
            })
        }
        root.addView(bar)
    }

    private fun renderAuth() {
        clear()
        header("Cardbook")
        val scroll = ScrollView(this)
        val box = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(22), dp(26), dp(22), dp(26))
        }
        scroll.addView(box)
        root.addView(scroll, LinearLayout.LayoutParams(-1, 0, 1f))

        box.addView(title("Tarjetas digitales inteligentes"))
        box.addView(paragraph("Accede a tus empresas, perfiles, tarjetas de presentacion, Book, alianzas y estadisticas desde Android."))

        val apiBase = input("API base URL", session.baseUrl.ifBlank { BuildConfig.CARDBOOK_API_BASE_URL }, false)
        val username = input("Usuario", "", false)
        val email = input("Email para registro", "", false)
        val password = input("Password", "", true)
        val status = paragraph("")

        box.addView(card().apply {
            addView(label("Conexion"))
            addView(apiBase)
            addView(label("Cuenta"))
            addView(username)
            addView(email)
            addView(password)
            val actions = LinearLayout(context).apply {
                orientation = LinearLayout.HORIZONTAL
                gravity = Gravity.CENTER
            }
            actions.addView(actionButton("Entrar", GOLD, BLUE_DARK) {
                session.baseUrl = apiBase.text.toString().trim()
                runAuth(status, username.text.toString(), password.text.toString(), false, email.text.toString())
            })
            actions.addView(space(10, 1))
            actions.addView(actionButton("Crear cuenta", BLUE, WHITE) {
                session.baseUrl = apiBase.text.toString().trim()
                runAuth(status, username.text.toString(), password.text.toString(), true, email.text.toString())
            })
            addView(actions)
            addView(status)
        })
    }

    private fun runAuth(status: TextView, username: String, password: String, register: Boolean, email: String) {
        status.text = "Conectando..."
        Thread {
            try {
                val payload = JSONObject().put("username", username).put("password", password)
                if (register) {
                    payload.put("email", email.ifBlank { "$username@cardbook.local" })
                    payload.put("password2", password)
                    payload.put("first_name", username)
                }
                val response = if (register) api.post("/api/v1/accounts/register/", payload, false) else api.post("/api/v1/accounts/login/", payload, false)
                val data = response.optJSONObject("data") ?: response
                val tokens = data.optJSONObject("tokens") ?: data
                session.accessToken = tokens.optString("access")
                session.refreshToken = tokens.optString("refresh")
                runOnUiThread { renderDashboard("Resumen") }
            } catch (e: Exception) {
                runOnUiThread { status.text = e.message ?: "No se pudo autenticar." }
            }
        }.start()
    }

    private fun renderDashboard(active: String) {
        clear()
        header("Cardbook", true)
        val shell = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL }
        root.addView(shell, LinearLayout.LayoutParams(-1, 0, 1f))

        val tabs = HorizontalScrollView(this)
        val row = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            setPadding(dp(12), dp(12), dp(12), dp(10))
        }
        val sections = listOf("Resumen", "Empresas", "Perfiles", "Tarjetas", "Book", "Publicaciones", "Alianzas")
        sections.forEach { item ->
            row.addView(chip(item, item == active) { renderDashboard(item) })
        }
        tabs.addView(row)
        shell.addView(tabs)

        val scroll = ScrollView(this)
        content = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(16), dp(8), dp(16), dp(22))
        }
        scroll.addView(content)
        shell.addView(scroll, LinearLayout.LayoutParams(-1, 0, 1f))

        when (active) {
            "Resumen" -> renderOverview()
            "Empresas" -> loadList("Empresas", "/api/v1/companies/")
            "Perfiles" -> loadList("Perfil del negocio", "/api/v1/cards/")
            "Tarjetas" -> loadList("Tarjetas de presentacion", "/api/v1/cards/business-cards/")
            "Book" -> loadList("Book", "/api/v1/book/")
            "Publicaciones" -> loadList("Publicaciones", "/api/v1/posts/")
            "Alianzas" -> loadList("Alianzas", "/api/v1/alliances/")
        }
    }

    private fun renderOverview() {
        content.addView(title("Panel movil"))
        content.addView(paragraph("Gestiona Cardbook desde Android conectado a tu API Django REST."))
        content.addView(metric("Empresas", "/api/v1/companies/"))
        content.addView(metric("Perfiles digitales", "/api/v1/cards/"))
        content.addView(metric("Guardados en Book", "/api/v1/book/"))
        content.addView(card().apply {
            addView(label("Accesos rapidos"))
            addView(paragraph("Empresas sugeridas, reacciones Eficiente, solicitudes de alianza, perfiles publicos y tarjetas guardadas quedan disponibles desde las secciones superiores."))
        })
    }

    private fun metric(label: String, endpoint: String): View {
        val value = TextView(this).apply {
            text = "..."
            setTextColor(BLUE_DARK)
            textSize = 32f
            typeface = Typeface.DEFAULT_BOLD
        }
        val panel = card().apply {
            addView(label(label))
            addView(value)
        }
        Thread {
            try {
                val json = api.get(endpoint)
                val count = extractArray(json)?.length() ?: json.optInt("count", 0)
                runOnUiThread { value.text = count.toString() }
            } catch (_: Exception) {
                runOnUiThread { value.text = "0" }
            }
        }.start()
        return panel
    }

    private fun loadStatic(title: String, message: String) {
        content.addView(title(title))
        content.addView(card().apply { addView(paragraph(message)) })
    }

    private fun loadList(titleText: String, endpoint: String) {
        content.addView(title(titleText))
        val progress = ProgressBar(this)
        content.addView(progress)
        Thread {
            try {
                val response = api.get(endpoint)
                val items = extractArray(response) ?: JSONArray()
                runOnUiThread {
                    content.removeView(progress)
                    if (items.length() == 0) content.addView(emptyState("No hay datos todavia."))
                    for (i in 0 until items.length()) {
                        val item = items.optJSONObject(i) ?: JSONObject()
                        content.addView(jsonCard(item))
                    }
                }
            } catch (e: Exception) {
                runOnUiThread {
                    content.removeView(progress)
                    content.addView(emptyState(e.message ?: "No se pudo cargar."))
                }
            }
        }.start()
    }

    private fun extractArray(response: JSONObject): JSONArray? {
        val data = response.opt("data")
        if (data is JSONArray) return data
        if (data is JSONObject) {
            val results = data.opt("results")
            if (results is JSONArray) return results
        }
        val results = response.opt("results")
        return if (results is JSONArray) results else null
    }

    private fun jsonCard(item: JSONObject): LinearLayout {
        val name = firstNonBlank(item, "name", "display_name", "company_name", "title", "business_name", "slug")
        val subtitle = firstNonBlank(item, "description", "job_title", "category", "email", "status", "created_at")
        return card().apply {
            addView(label(name.ifBlank { "Registro" }))
            if (subtitle.isNotBlank()) addView(paragraph(subtitle))
            val meta = mutableListOf<String>()
            listOf("phone", "website", "city", "efficient_count").forEach { key ->
                if (item.has(key) && !item.isNull(key)) meta.add("$key: ${item.optString(key)}")
            }
            if (meta.isNotEmpty()) addView(small(meta.joinToString("  |  ")))
        }
    }

    private fun firstNonBlank(item: JSONObject, vararg keys: String): String {
        keys.forEach { key ->
            val value = item.optString(key, "")
            if (value.isNotBlank() && value != "null") return value
        }
        return ""
    }

    private fun input(hint: String, value: String, secret: Boolean): EditText {
        return EditText(this).apply {
            this.hint = hint
            setText(value)
            setSingleLine(true)
            textSize = 15f
            setPadding(dp(14), dp(10), dp(14), dp(10))
            background = rounded(WHITE, 1, 0x220057B8)
            inputType = if (secret) InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_VARIATION_PASSWORD else InputType.TYPE_CLASS_TEXT
            layoutParams = LinearLayout.LayoutParams(-1, LinearLayout.LayoutParams.WRAP_CONTENT).apply { setMargins(0, dp(6), 0, dp(12)) }
        }
    }

    private fun title(text: String) = TextView(this).apply {
        this.text = text
        setTextColor(BLUE_DARK)
        textSize = 26f
        typeface = Typeface.DEFAULT_BOLD
        setPadding(0, dp(8), 0, dp(6))
    }

    private fun label(text: String) = TextView(this).apply {
        this.text = text
        setTextColor(INK)
        textSize = 17f
        typeface = Typeface.DEFAULT_BOLD
        setPadding(0, dp(6), 0, dp(2))
    }

    private fun paragraph(text: String) = TextView(this).apply {
        this.text = text
        setTextColor(MUTED)
        textSize = 15f
        setPadding(0, dp(2), 0, dp(10))
    }

    private fun small(text: String) = TextView(this).apply {
        this.text = text
        setTextColor(BLUE)
        textSize = 13f
        setPadding(0, dp(4), 0, 0)
    }

    private fun emptyState(text: String) = card().apply { addView(paragraph(text)) }

    private fun card() = LinearLayout(this).apply {
        orientation = LinearLayout.VERTICAL
        setPadding(dp(18), dp(16), dp(18), dp(16))
        background = rounded(WHITE, 1, 0x110057B8)
        layoutParams = LinearLayout.LayoutParams(-1, LinearLayout.LayoutParams.WRAP_CONTENT).apply { setMargins(0, dp(8), 0, dp(12)) }
        elevation = dp(2).toFloat()
    }

    private fun chip(text: String, active: Boolean, onClick: () -> Unit) = Button(this).apply {
        this.text = text
        setTextColor(if (active) WHITE else BLUE_DARK)
        typeface = Typeface.DEFAULT_BOLD
        textSize = 13f
        background = rounded(if (active) BLUE else WHITE, 1, if (active) BLUE else 0x220057B8)
        setOnClickListener { onClick() }
        layoutParams = LinearLayout.LayoutParams(LinearLayout.LayoutParams.WRAP_CONTENT, dp(44)).apply { setMargins(0, 0, dp(8), 0) }
    }

    private fun actionButton(text: String, bg: Int, fg: Int, onClick: () -> Unit) = Button(this).apply {
        this.text = text
        setTextColor(fg)
        textSize = 14f
        typeface = Typeface.DEFAULT_BOLD
        background = rounded(bg, 0, bg)
        setOnClickListener { onClick() }
    }

    private fun space(w: Int, h: Int) = View(this).apply { layoutParams = LinearLayout.LayoutParams(dp(w), dp(h)) }

    private fun rounded(color: Int, strokeWidth: Int, strokeColor: Int): GradientDrawable {
        return GradientDrawable().apply {
            setColor(color)
            cornerRadius = dp(12).toFloat()
            if (strokeWidth > 0) setStroke(dp(strokeWidth), strokeColor)
        }
    }

    private fun gradient(start: Int, end: Int): GradientDrawable {
        return GradientDrawable(GradientDrawable.Orientation.LEFT_RIGHT, intArrayOf(start, end))
    }

    private fun dp(value: Int): Int = (value * resources.displayMetrics.density).toInt()
}

class SessionStore(context: Context) {
    private val prefs = context.getSharedPreferences("cardbook_session", Context.MODE_PRIVATE)

    var baseUrl: String
        get() = prefs.getString("base_url", BuildConfig.CARDBOOK_API_BASE_URL) ?: BuildConfig.CARDBOOK_API_BASE_URL
        set(value) = prefs.edit().putString("base_url", value.trimEnd('/')).apply()

    var accessToken: String?
        get() = prefs.getString("access", null)
        set(value) = prefs.edit().putString("access", value).apply()

    var refreshToken: String?
        get() = prefs.getString("refresh", null)
        set(value) = prefs.edit().putString("refresh", value).apply()

    fun clear() {
        val currentBase = baseUrl
        prefs.edit().clear().putString("base_url", currentBase).apply()
    }
}

class CardbookApi(private val session: SessionStore) {
    fun get(path: String): JSONObject = request("GET", path, null, true)
    fun post(path: String, body: JSONObject, auth: Boolean = true): JSONObject = request("POST", path, body, auth)

    private fun request(method: String, path: String, body: JSONObject?, auth: Boolean): JSONObject {
        val url = URL(session.baseUrl.trimEnd('/') + path)
        val connection = (url.openConnection() as HttpURLConnection).apply {
            requestMethod = method
            connectTimeout = 15000
            readTimeout = 15000
            setRequestProperty("Accept", "application/json")
            setRequestProperty("Content-Type", "application/json")
            if (auth && !session.accessToken.isNullOrBlank()) setRequestProperty("Authorization", "Bearer ${session.accessToken}")
            if (body != null) doOutput = true
        }
        if (body != null) {
            OutputStreamWriter(connection.outputStream).use { it.write(body.toString()) }
        }
        val stream = if (connection.responseCode in 200..299) connection.inputStream else connection.errorStream
        val text = BufferedReader(InputStreamReader(stream)).use { it.readText() }
        if (connection.responseCode !in 200..299) throw IllegalStateException(text.ifBlank { "HTTP ${connection.responseCode}" })
        return if (text.isBlank()) JSONObject() else JSONObject(text)
    }
}

