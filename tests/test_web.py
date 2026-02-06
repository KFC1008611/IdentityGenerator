"""Tests for Flask web UI."""

from identity_gen.web import create_app, _parse_count, run_web_server


class TestWebUI:
    """Tests for web GUI behavior."""

    def test_index_page(self):
        """Index page should load successfully."""
        app = create_app(default_count=3)
        client = app.test_client()

        response = client.get("/")

        assert response.status_code == 200
        html = response.get_data(as_text=True)
        assert "中文身份信息生成器 Web 界面" in html
        assert 'name="fields"' in html
        assert "生成身份证图片（特殊选项）" in html
        assert 'value="table"' not in html

    def test_generate_preview_with_selected_fields(self):
        """Generate endpoint should return preview for selected columns."""
        app = create_app(default_count=2)
        client = app.test_client()

        response = client.post(
            "/generate",
            data={
                "count": "2",
                "seed": "42",
                "format": "json",
                "fields": ["name", "email", "phone"],
            },
        )

        assert response.status_code == 200
        html = response.get_data(as_text=True)
        assert "共生成 2 条" in html
        assert "格式化结果" in html
        assert '"name"' in html
        assert '"email"' in html

    def test_generate_with_idcard_option(self, monkeypatch):
        """Generate endpoint should support ID card option and backend selection."""
        captured = {}

        def fake_generate_batch(
            self,
            identities,
            output_dir,
            filename_pattern,
            include_avatar=True,
            avatar_backend="auto",
        ):
            captured["count"] = len(identities)
            captured["output_dir"] = str(output_dir)
            captured["filename_pattern"] = filename_pattern
            captured["include_avatar"] = include_avatar
            captured["avatar_backend"] = avatar_backend
            return [output_dir / "demo_0000.png", output_dir / "demo_0001.png"]

        monkeypatch.setattr(
            "identity_gen.idcard_image_generator.IDCardImageGenerator.generate_batch",
            fake_generate_batch,
        )

        app = create_app(default_count=2)
        client = app.test_client()

        response = client.post(
            "/generate",
            data={
                "count": "2",
                "format": "json",
                "fields": ["name", "ssn"],
                "idcard_enabled": "1",
                "avatar_backend": "random_face",
                "idcard_dir": "idcards/web-test",
            },
        )

        assert response.status_code == 200
        html = response.get_data(as_text=True)
        assert "已生成 2 张身份证图片" in html
        assert captured["count"] == 2
        assert captured["output_dir"].endswith("idcards/web-test")
        assert captured["include_avatar"] is True
        assert captured["avatar_backend"] == "random_face"

    def test_generate_rejects_idcard_dir_path_traversal(self, monkeypatch):
        """Web endpoint should reject idcard_dir outside trusted base path."""
        called = {"value": False}

        def fake_generate_batch(self, *args, **kwargs):
            called["value"] = True
            return []

        monkeypatch.setattr(
            "identity_gen.idcard_image_generator.IDCardImageGenerator.generate_batch",
            fake_generate_batch,
        )

        app = create_app(default_count=1)
        client = app.test_client()

        response = client.post(
            "/generate",
            data={
                "count": "1",
                "format": "json",
                "idcard_enabled": "1",
                "avatar_backend": "no_avatar",
                "idcard_dir": "../outside-dir",
            },
        )

        assert response.status_code == 200
        html = response.get_data(as_text=True)
        assert "生成失败" in html
        assert "idcard_dir 必须位于 idcards 目录内" in html
        assert called["value"] is False

    def test_download_generated_content(self):
        """Download endpoint should return attachment with selected format extension."""
        app = create_app(default_count=1)
        client = app.test_client()

        response = client.post(
            "/download",
            data={"content": '{"name":"张三"}', "format": "json"},
        )

        assert response.status_code == 200
        disposition = response.headers.get("Content-Disposition", "")
        assert "attachment;" in disposition
        assert disposition.endswith('.json"')
        assert response.headers.get("Content-Type") == "application/json; charset=utf-8"
        assert response.get_data(as_text=True) == '{"name":"张三"}'

    def test_download_fallback_format_and_parse_count(self):
        app = create_app(default_count=7)
        client = app.test_client()

        response = client.post(
            "/download",
            data={"content": "abc", "format": "unknown"},
        )
        assert response.status_code == 200
        assert response.headers.get("Content-Type") == "application/json; charset=utf-8"

        assert _parse_count("", 7) == 7

    def test_run_web_server_wrapper(self, monkeypatch):
        called = {}

        class _App:
            def run(self, **kwargs):
                called.update(kwargs)

        monkeypatch.setattr("identity_gen.web.create_app", lambda: _App())
        run_web_server(host="0.0.0.0", port=1234)
        assert called == {
            "host": "0.0.0.0",
            "port": 1234,
            "debug": False,
            "use_reloader": False,
        }

    def test_generate_error_branch(self):
        app = create_app(default_count=1)
        client = app.test_client()
        response = client.post("/generate", data={"count": "bad", "format": "json"})
        assert response.status_code == 200
        assert "生成失败" in response.get_data(as_text=True)
