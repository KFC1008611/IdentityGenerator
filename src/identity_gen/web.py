"""Flask web UI for identity generation."""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set

from flask import Flask, render_template_string, request

from .formatters import IdentityFormatter
from .generator import IdentityGenerator
from .idcard_image_generator import IDCardImageGenerator
from .models import IdentityConfig, IdentityField, OutputFormat

WEB_OUTPUT_FORMATS = (
    OutputFormat.JSON,
    OutputFormat.CSV,
    OutputFormat.RAW,
    OutputFormat.SQL,
    OutputFormat.MARKDOWN,
    OutputFormat.YAML,
    OutputFormat.VCARD,
)

FORMAT_EXTENSIONS = {
    OutputFormat.JSON.value: "json",
    OutputFormat.CSV.value: "csv",
    OutputFormat.RAW.value: "txt",
    OutputFormat.SQL.value: "sql",
    OutputFormat.MARKDOWN.value: "md",
    OutputFormat.YAML.value: "yaml",
    OutputFormat.VCARD.value: "vcf",
}

FORMAT_MIME_TYPES = {
    OutputFormat.JSON.value: "application/json; charset=utf-8",
    OutputFormat.CSV.value: "text/csv; charset=utf-8",
    OutputFormat.RAW.value: "text/plain; charset=utf-8",
    OutputFormat.SQL.value: "application/sql; charset=utf-8",
    OutputFormat.MARKDOWN.value: "text/markdown; charset=utf-8",
    OutputFormat.YAML.value: "application/yaml; charset=utf-8",
    OutputFormat.VCARD.value: "text/vcard; charset=utf-8",
}

FIELD_LABELS = {
    "name": "姓名",
    "first_name": "名",
    "last_name": "姓",
    "gender": "性别",
    "birthdate": "出生日期",
    "ssn": "身份证号",
    "ethnicity": "民族",
    "blood_type": "血型",
    "height": "身高",
    "weight": "体重",
    "email": "邮箱",
    "phone": "手机号",
    "address": "地址",
    "city": "城市",
    "state": "省份",
    "zipcode": "邮编",
    "country": "国家",
    "company": "公司",
    "job_title": "职位",
    "education": "学历",
    "major": "专业",
    "username": "用户名",
    "password": "密码",
    "wechat_id": "微信号",
    "qq_number": "QQ号",
    "political_status": "政治面貌",
    "marital_status": "婚姻状况",
    "religion": "宗教信仰",
    "bank_card": "银行卡号",
    "license_plate": "车牌号",
    "social_credit_code": "统一社会信用代码",
    "ip_address": "IP地址",
    "mac_address": "MAC地址",
    "zodiac_sign": "星座",
    "chinese_zodiac": "生肖",
    "emergency_contact": "紧急联系人",
    "emergency_phone": "紧急联系电话",
    "hobbies": "兴趣爱好",
}

AVATAR_BACKEND_OPTIONS = [
    {"value": "auto", "label": "自动选择"},
    {"value": "ark", "label": "火山方舟 (ARK)"},
    {"value": "diffusers", "label": "AI 模型 (diffusers)"},
    {"value": "random_face", "label": "random_face"},
    {"value": "fallback", "label": "备用剪影"},
    {"value": "no_avatar", "label": "不生成头像"},
]

PAGE_TEMPLATE = """
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>中文身份信息生成器</title>
  <style>
    :root {
      --bg-top: #f4f8ff;
      --bg-bottom: #eef5ef;
      --ink: #1f2937;
      --muted: #4b5563;
      --brand: #0f766e;
      --brand-2: #0ea5e9;
      --surface: #ffffff;
      --border: #d1d5db;
      --shadow: rgba(15, 118, 110, 0.14);
    }

    * { box-sizing: border-box; }

    body {
      margin: 0;
      font-family: "PingFang SC", "Hiragino Sans GB", "Noto Sans SC", sans-serif;
      color: var(--ink);
      background: radial-gradient(circle at 10% 10%, #ffffff 0%, transparent 40%),
                  linear-gradient(165deg, var(--bg-top) 0%, var(--bg-bottom) 100%);
      min-height: 100vh;
      padding: 24px;
    }

    .layout {
      width: min(1200px, 100%);
      margin: 0 auto;
      display: grid;
      gap: 18px;
    }

    .card {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 14px;
      box-shadow: 0 10px 30px var(--shadow);
      padding: 18px;
    }

    h1 {
      margin: 0;
      font-size: clamp(1.4rem, 2vw, 2rem);
      letter-spacing: 0.02em;
    }

    .subtitle {
      margin: 8px 0 0;
      color: var(--muted);
      font-size: 0.95rem;
    }

    .form-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 12px;
      margin-bottom: 14px;
    }

    label {
      display: block;
      font-size: 0.88rem;
      color: var(--muted);
      margin-bottom: 6px;
    }

    input[type="number"],
    select {
      width: 100%;
      padding: 9px 10px;
      border-radius: 9px;
      border: 1px solid var(--border);
      font-size: 0.95rem;
      background: #fff;
    }

    .fields {
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 12px;
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
      gap: 8px;
      max-height: 300px;
      overflow: auto;
      background: #fcfefe;
    }

    .checkbox-row {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 0.9rem;
      color: #1f2937;
      margin: 0;
    }

    .actions {
      margin-top: 14px;
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      align-items: center;
    }

    .special-options {
      margin: 14px 0;
      padding: 12px;
      border: 1px dashed var(--border);
      border-radius: 10px;
      background: #f8fbff;
    }

    button {
      border: none;
      border-radius: 10px;
      padding: 10px 16px;
      font-size: 0.95rem;
      font-weight: 600;
      color: #fff;
      background: linear-gradient(125deg, var(--brand), var(--brand-2));
      cursor: pointer;
    }

    .hint {
      font-size: 0.86rem;
      color: var(--muted);
    }

    .error {
      color: #b91c1c;
      background: #fee2e2;
      border: 1px solid #fecaca;
      border-radius: 10px;
      padding: 10px;
      margin-top: 10px;
    }

    .preview-meta {
      margin: 0 0 10px;
      color: var(--muted);
      font-size: 0.9rem;
    }

    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 0.88rem;
      overflow: hidden;
      border-radius: 10px;
    }

    th, td {
      border: 1px solid var(--border);
      text-align: left;
      padding: 7px 8px;
      vertical-align: top;
      word-break: break-word;
    }

    th {
      background: #effdfa;
      position: sticky;
      top: 0;
      z-index: 1;
    }

    .table-wrap {
      overflow: auto;
      max-height: 420px;
    }

    textarea {
      width: 100%;
      min-height: 210px;
      margin-top: 10px;
      border-radius: 10px;
      border: 1px solid var(--border);
      padding: 10px;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
      font-size: 0.82rem;
      line-height: 1.45;
      resize: vertical;
    }
  </style>
</head>
<body>
  <main class="layout">
    <section class="card">
      <h1>中文身份信息生成器 Web 界面</h1>
      <p class="subtitle">可选生成字段，提交后即时预览数据。</p>
    </section>

    <section class="card">
      <form method="post" action="/generate">
        <div class="form-grid">
          <div>
            <label for="count">生成数量 (1-10000)</label>
            <input id="count" name="count" type="number" min="1" max="10000" value="{{ count }}" required>
          </div>
          <div>
            <label for="seed">随机种子 (可选)</label>
            <input id="seed" name="seed" type="number" value="{{ seed }}" placeholder="不填则随机">
          </div>
          <div>
            <label for="format">格式化预览</label>
            <select id="format" name="format">
              {% for fmt in formats %}
              <option value="{{ fmt.value }}" {% if selected_format == fmt.value %}selected{% endif %}>{{ fmt.value }}</option>
              {% endfor %}
            </select>
          </div>
        </div>

        <label>输出字段（可多选；若不选则默认全部字段）</label>
        <div class="fields">
          {% for field in fields %}
          <label class="checkbox-row">
            <input type="checkbox" name="fields" value="{{ field.value }}" {% if field.value in selected_fields %}checked{% endif %}>
            <span>{{ field.label }}</span>
          </label>
          {% endfor %}
        </div>

        <div class="special-options">
          <label class="checkbox-row">
            <input type="checkbox" name="idcard_enabled" value="1" {% if idcard_enabled %}checked{% endif %}>
            <span>生成身份证图片（特殊选项）</span>
          </label>
          <div class="form-grid" style="margin-top:10px; margin-bottom:0;">
            <div>
              <label for="avatar_backend">身份证头像生成方式</label>
              <select id="avatar_backend" name="avatar_backend">
                {% for opt in avatar_backends %}
                <option value="{{ opt.value }}" {% if selected_avatar_backend == opt.value %}selected{% endif %}>{{ opt.label }}</option>
                {% endfor %}
              </select>
            </div>
            <div>
              <label for="idcard_dir">身份证图片输出目录</label>
              <input id="idcard_dir" name="idcard_dir" type="text" value="{{ idcard_dir }}" placeholder="idcards/web">
            </div>
          </div>
        </div>

        <div class="actions">
          <button type="submit">生成并预览</button>
          <span class="hint">预览最多显示前 20 条，完整结果在格式化区域中可复制。</span>
        </div>
      </form>
      {% if error %}
      <div class="error">{{ error }}</div>
      {% endif %}
    </section>

    {% if preview_rows is not none %}
    <section class="card">
      <p class="preview-meta">共生成 {{ total_count }} 条，当前展示前 {{ shown_count }} 条。</p>
      {% if preview_rows %}
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              {% for col in columns %}
              <th>{{ col }}</th>
              {% endfor %}
            </tr>
          </thead>
          <tbody>
            {% for row in preview_rows %}
            <tr>
              {% for col in columns %}
              <td>{{ row.get(col, '') }}</td>
              {% endfor %}
            </tr>
            {% endfor %}
          </tbody>
        </table>
      </div>
      {% else %}
      <p class="hint">未生成可预览数据。</p>
      {% endif %}

      <label for="formatted">格式化结果</label>
      <textarea id="formatted" readonly>{{ formatted_output }}</textarea>

      {% if formatted_output %}
      <form method="post" action="/download" style="margin-top:10px;">
        <textarea name="content" style="display:none;">{{ formatted_output }}</textarea>
        <input type="hidden" name="format" value="{{ selected_format }}">
        <button type="submit">下载当前结果</button>
      </form>
      {% endif %}

      {% if generated_idcards %}
      <p class="preview-meta" style="margin-top:12px;">已生成 {{ generated_idcards|length }} 张身份证图片（展示前 10 条路径）：</p>
      <textarea readonly>{% for path in generated_idcards %}{{ path }}
{% endfor %}</textarea>
      {% endif %}
    </section>
    {% endif %}
  </main>
</body>
</html>
"""


def _parse_count(raw_value: Optional[str], default: int) -> int:
    if not raw_value:
        return default
    return max(1, min(10000, int(raw_value)))


def _parse_seed(raw_value: Optional[str]) -> Optional[int]:
    if not raw_value:
        return None
    return int(raw_value)


def _default_context(default_count: int) -> Dict[str, object]:
    default_fields = {field.value for field in IdentityField}
    field_options = [
        {"value": field.value, "label": FIELD_LABELS.get(field.value, field.value)}
        for field in IdentityField
    ]
    return {
        "count": default_count,
        "seed": "",
        "formats": WEB_OUTPUT_FORMATS,
        "selected_format": OutputFormat.JSON.value,
        "fields": field_options,
        "selected_fields": default_fields,
        "preview_rows": None,
        "columns": [],
        "formatted_output": "",
        "idcard_enabled": False,
        "avatar_backends": AVATAR_BACKEND_OPTIONS,
        "selected_avatar_backend": "auto",
        "idcard_dir": "idcards/web",
        "generated_idcards": [],
        "total_count": 0,
        "shown_count": 0,
        "error": "",
    }


def create_app(default_count: int = 10) -> Flask:
    """Create Flask application for web UI."""
    app = Flask(__name__)

    @app.get("/")
    def index() -> str:
        return render_template_string(PAGE_TEMPLATE, **_default_context(default_count))

    @app.post("/generate")
    def generate() -> str:
        context = _default_context(default_count)

        context["count"] = request.form.get("count", str(default_count))
        context["seed"] = request.form.get("seed", "")
        selected_format = request.form.get("format", OutputFormat.JSON.value)
        selected_fields = set(request.form.getlist("fields"))
        idcard_enabled = request.form.get("idcard_enabled") == "1"
        selected_avatar_backend = request.form.get("avatar_backend", "auto")
        idcard_dir = (
            request.form.get("idcard_dir", "idcards/web").strip() or "idcards/web"
        )
        context["selected_format"] = selected_format
        context["selected_fields"] = selected_fields
        context["idcard_enabled"] = idcard_enabled
        context["selected_avatar_backend"] = selected_avatar_backend
        context["idcard_dir"] = idcard_dir

        try:
            output_format = OutputFormat(selected_format)
            count = _parse_count(request.form.get("count"), default_count)
            seed = _parse_seed(request.form.get("seed"))

            include_fields: Optional[List[str]]
            include_fields = sorted(selected_fields) if selected_fields else None

            config = IdentityConfig(
                locale="zh_CN",
                count=count,
                include_fields=include_fields,
                seed=seed,
                format=output_format,
            )

            generator = IdentityGenerator(config)
            identities = generator.generate_batch()
            formatter = IdentityFormatter()
            effective_fields: Set[str] = config.get_effective_fields()

            preview_limit = 20
            preview_rows = [
                identity.to_dict(effective_fields)
                for identity in identities[:preview_limit]
            ]
            columns = (
                list(preview_rows[0].keys())
                if preview_rows
                else sorted(effective_fields)
            )

            context["count"] = count
            context["preview_rows"] = preview_rows
            context["columns"] = columns
            context["formatted_output"] = formatter.format(
                identities,
                config.format,
                config.get_effective_fields(),
            )

            if idcard_enabled:
                include_avatar = selected_avatar_backend != "no_avatar"
                avatar_backend = (
                    "auto" if not include_avatar else selected_avatar_backend
                )

                idcard_output = Path(idcard_dir)
                idcard_output.mkdir(parents=True, exist_ok=True)
                idcard_generator = IDCardImageGenerator()
                base_name = f"web_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                pattern = f"{base_name}_{{index:04d}}.png"
                saved_files = idcard_generator.generate_batch(
                    identities=identities,
                    output_dir=idcard_output,
                    filename_pattern=pattern,
                    include_avatar=include_avatar,
                    avatar_backend=avatar_backend,
                )
                context["generated_idcards"] = [str(path) for path in saved_files[:10]]

            context["total_count"] = len(identities)
            context["shown_count"] = len(preview_rows)
        except Exception as exc:
            context["error"] = f"生成失败: {exc}"

        return render_template_string(PAGE_TEMPLATE, **context)

    @app.post("/download")
    def download() -> tuple[bytes, int, dict[str, str]]:
        content = request.form.get("content", "")
        output_format = request.form.get("format", OutputFormat.JSON.value)
        if output_format not in FORMAT_EXTENSIONS:
            output_format = OutputFormat.JSON.value

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"identities_{timestamp}.{FORMAT_EXTENSIONS[output_format]}"
        payload = content.encode("utf-8")
        headers = {
            "Content-Type": FORMAT_MIME_TYPES[output_format],
            "Content-Disposition": f'attachment; filename="{filename}"',
        }
        return payload, 200, headers

    return app


def run_web_server(host: str = "127.0.0.1", port: int = 5000) -> None:
    """Run Flask web server for GUI mode."""
    app = create_app()
    app.run(host=host, port=port, debug=False, use_reloader=False)
