from __future__ import annotations

import html
import sys
from pathlib import Path

from PySide6.QtCore import QObject, Qt, QThread, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QStatusBar,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from link_detector import find_links
from ocr_core import SUPPORTED_IMAGE_SUFFIXES, detect_links_from_rows, run_ocr_on_image_path

APP_TITLE = "HuaShengOCR"


class OCRWorker(QObject):
    finished = Signal(list, str, bool, list)
    failed = Signal(str)

    def __init__(self, image_path: Path) -> None:
        super().__init__()
        self.image_path = image_path

    def run(self) -> None:
        try:
            rows, full_text = run_ocr_on_image_path(self.image_path)
            matched, links = detect_links_from_rows(rows, full_text)
            self.finished.emit(rows, full_text, matched, links)
        except Exception as exc:
            self.failed.emit(str(exc))


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.resize(1280, 860)
        self.selected_path: Path | None = None
        self.worker_thread: QThread | None = None
        self.current_hit_rows: list[dict] = []
        self.current_links: list[str] = []

        self.file_label = QLabel("未选择文件")
        self.file_label.setWordWrap(True)

        self.summary_label = QLabel("识别结果会显示在这里")
        self.summary_label.setWordWrap(True)
        self.summary_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        self.preview_label = QLabel("请选择图片")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumWidth(360)
        self.preview_label.setStyleSheet("border: 1px solid #ccc; background: #fafafa;")

        self.audit_status_label = QLabel("待识别")
        self.audit_status_label.setAlignment(Qt.AlignCenter)
        self.audit_status_label.setMinimumHeight(42)
        self.audit_status_label.setStyleSheet(
            "font-weight: 700; border-radius: 8px; padding: 8px; background: #f3f4f6; color: #111827;"
        )

        self.audit_metrics_label = QLabel("命中 0 处文本块 / 0 个链接")
        self.audit_metrics_label.setWordWrap(True)

        self.review_decision_label = QLabel("人工审核结论：未标记")
        self.review_decision_label.setWordWrap(True)
        self.review_decision_label.setStyleSheet(
            "font-weight: 700; border-radius: 8px; padding: 8px; background: #f3f4f6; color: #111827;"
        )

        self.audit_hits_text = QTextEdit()
        self.audit_hits_text.setReadOnly(True)
        self.audit_hits_text.setPlaceholderText("命中的文本块会显示在这里")

        self.audit_links_text = QTextEdit()
        self.audit_links_text.setReadOnly(True)
        self.audit_links_text.setPlaceholderText("检测到的链接会显示在这里")

        self.text_output = QTextEdit()
        self.text_output.setReadOnly(True)
        self.detail_output = QTextEdit()
        self.detail_output.setReadOnly(True)

        self.choose_button = QPushButton("选择图片")
        self.run_button = QPushButton("开始识别")
        self.clear_button = QPushButton("清空结果")
        self.approve_button = QPushButton("审核通过")
        self.reject_button = QPushButton("审核拒绝")
        self.pending_button = QPushButton("待复核")

        self.choose_button.clicked.connect(self.choose_image)
        self.run_button.clicked.connect(self.start_ocr)
        self.clear_button.clicked.connect(self.clear_results)
        self.approve_button.clicked.connect(lambda: self.set_review_decision("审核通过", "#dcfce7", "#166534"))
        self.reject_button.clicked.connect(lambda: self.set_review_decision("审核拒绝", "#fee2e2", "#b91c1c"))
        self.pending_button.clicked.connect(lambda: self.set_review_decision("待复核", "#fef3c7", "#92400e"))

        self._build_ui()

        status = QStatusBar()
        status.showMessage("就绪：请选择一张图片开始识别")
        self.setStatusBar(status)
        self._set_review_buttons_enabled(False)

    def _build_ui(self) -> None:
        top_bar = QHBoxLayout()
        top_bar.addWidget(self.choose_button)
        top_bar.addWidget(self.run_button)
        top_bar.addWidget(self.clear_button)
        top_bar.addWidget(self.file_label, 1)

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.addWidget(QLabel("图片预览"))
        left_layout.addWidget(self.preview_label, 1)

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.addWidget(QLabel("识别摘要"))
        right_layout.addWidget(self.summary_label)

        audit_frame = QFrame()
        audit_frame.setFrameShape(QFrame.StyledPanel)
        audit_frame.setStyleSheet("QFrame { background: #fcfcfd; border: 1px solid #d1d5db; border-radius: 10px; }")
        audit_layout = QVBoxLayout(audit_frame)
        audit_layout.addWidget(QLabel("人工审核区"))
        audit_layout.addWidget(self.audit_status_label)
        audit_layout.addWidget(self.audit_metrics_label)

        review_buttons = QHBoxLayout()
        review_buttons.addWidget(self.approve_button)
        review_buttons.addWidget(self.reject_button)
        review_buttons.addWidget(self.pending_button)
        audit_layout.addLayout(review_buttons)
        audit_layout.addWidget(self.review_decision_label)

        audit_layout.addWidget(QLabel("命中文本块（红色高亮）"))
        audit_layout.addWidget(self.audit_hits_text, 1)
        audit_layout.addWidget(QLabel("命中链接清单"))
        audit_layout.addWidget(self.audit_links_text, 1)
        right_layout.addWidget(audit_frame, 2)

        right_layout.addWidget(QLabel("完整文本"))
        right_layout.addWidget(self.text_output, 2)
        right_layout.addWidget(QLabel("明细结果"))
        right_layout.addWidget(self.detail_output, 2)

        splitter = QSplitter()
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([380, 860])

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.addLayout(top_bar)
        layout.addWidget(splitter, 1)
        self.setCentralWidget(central)

    def choose_image(self) -> None:
        file_filter = "图片文件 (*.png *.jpg *.jpeg *.webp *.bmp)"
        filename, _ = QFileDialog.getOpenFileName(self, "选择要识别的图片", "", file_filter)
        if not filename:
            return

        path = Path(filename)
        if path.suffix.lower() not in SUPPORTED_IMAGE_SUFFIXES:
            QMessageBox.critical(self, APP_TITLE, "暂不支持这个图片格式")
            return

        self.selected_path = path
        self.file_label.setText(f"当前文件：{path}")
        self.statusBar().showMessage("图片已选择，点击“开始识别”即可")
        self._show_preview(path)

    def _show_preview(self, path: Path) -> None:
        pixmap = QPixmap(str(path))
        if pixmap.isNull():
            self.preview_label.setText("图片预览失败")
            self.preview_label.setPixmap(QPixmap())
            return
        scaled = pixmap.scaled(460, 600, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.preview_label.setPixmap(scaled)
        self.preview_label.setText("")

    def start_ocr(self) -> None:
        if not self.selected_path:
            QMessageBox.information(self, APP_TITLE, "请先选择一张图片")
            return

        self.run_button.setEnabled(False)
        self.summary_label.setText("识别中…")
        self.text_output.clear()
        self.detail_output.clear()
        self.audit_hits_text.clear()
        self.audit_links_text.clear()
        self.current_hit_rows = []
        self.current_links = []
        self._set_audit_status("识别中，等待结果…", "#dbeafe", "#1d4ed8")
        self.audit_metrics_label.setText("命中 0 处文本块 / 0 个链接")
        self.set_review_decision("未标记", "#f3f4f6", "#111827", announce=False)
        self._set_review_buttons_enabled(False)
        self.statusBar().showMessage("正在识别，请稍等… 首次加载模型会更慢一些")

        self.worker_thread = QThread()
        worker = OCRWorker(self.selected_path)
        worker.moveToThread(self.worker_thread)
        self.worker_thread.started.connect(worker.run)
        worker.finished.connect(self._render_result)
        worker.failed.connect(self._render_error)
        worker.finished.connect(self.worker_thread.quit)
        worker.failed.connect(self.worker_thread.quit)
        worker.finished.connect(worker.deleteLater)
        worker.failed.connect(worker.deleteLater)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)
        self.worker_thread.finished.connect(lambda: self.run_button.setEnabled(True))
        self.worker_thread.start()

    def _render_result(self, rows: list, full_text: str, matched: bool, links: list) -> None:
        count = len(rows)
        hit_rows: list[dict] = []
        unique_links: list[str] = []

        for row in rows:
            row_links = find_links(row.get("text", ""))
            if row_links:
                hit_rows.append({**row, "matched_links": row_links})
                for link in row_links:
                    if link not in unique_links:
                        unique_links.append(link)

        for link in links:
            if link not in unique_links:
                unique_links.append(link)

        self.current_hit_rows = hit_rows
        self.current_links = unique_links

        hit_block_count = len(hit_rows)
        link_count = len(unique_links)

        summary_lines = [f"识别完成：共识别 {count} 段文本"]
        if matched:
            summary_lines.append(f"需要人工审核：命中 {hit_block_count} 处文本块 / {link_count} 个链接")
            self._set_audit_status("需要人工审核", "#fee2e2", "#b91c1c")
        else:
            summary_lines.append("基本通过：未检测到明显链接")
            self._set_audit_status("基本通过", "#dcfce7", "#166534")
        self.summary_label.setText("；".join(summary_lines))
        self.audit_metrics_label.setText(f"命中 {hit_block_count} 处文本块 / {link_count} 个链接")
        self._set_review_buttons_enabled(True)

        if hit_rows:
            self.audit_hits_text.setHtml(self._build_hit_rows_html(hit_rows))
        else:
            self.audit_hits_text.setPlainText("未发现带链接的文本块")

        if unique_links:
            self.audit_links_text.setPlainText("\n".join(f"- {link}" for link in unique_links))
        else:
            self.audit_links_text.setPlainText("未检测到链接")

        self.text_output.setPlainText(full_text or "（未识别到文本）")

        details: list[str] = []
        for idx, row in enumerate(rows, start=1):
            score = row.get("score")
            score_text = f"{score:.4f}" if isinstance(score, float) else "-"
            details.append(
                f"[{idx}] 置信度: {score_text}\n文本: {row.get('text', '')}\n坐标: {row.get('box', [])}\n"
            )
        self.detail_output.setPlainText("\n".join(details) if details else "（无明细结果）")
        self.statusBar().showMessage("识别完成，可以进行人工审核")

    def _build_hit_rows_html(self, hit_rows: list[dict]) -> str:
        blocks: list[str] = []
        for idx, row in enumerate(hit_rows, start=1):
            text = html.escape(str(row.get("text", "")))
            links = row.get("matched_links", [])
            links_html = "<br>".join(f"<span style='color:#b91c1c;'>• {html.escape(link)}</span>" for link in links)
            blocks.append(
                """
                <div style="margin-bottom:10px;padding:10px;border:1px solid #fecaca;border-radius:8px;background:#fef2f2;">
                    <div style="font-weight:700;color:#991b1b;">命中文本块 {idx}</div>
                    <div style="margin-top:6px;color:#7f1d1d;white-space:pre-wrap;">{text}</div>
                    <div style="margin-top:8px;font-size:12px;color:#b91c1c;">{links_html}</div>
                </div>
                """.replace("{idx}", str(idx)).replace("{text}", text).replace("{links_html}", links_html)
            )
        return "<html><body>" + "".join(blocks) + "</body></html>"

    def _set_audit_status(self, text: str, bg_color: str, fg_color: str) -> None:
        self.audit_status_label.setText(text)
        self.audit_status_label.setStyleSheet(
            f"font-weight: 700; border-radius: 8px; padding: 8px; background: {bg_color}; color: {fg_color};"
        )

    def set_review_decision(self, text: str, bg_color: str, fg_color: str, announce: bool = True) -> None:
        self.review_decision_label.setText(f"人工审核结论：{text}")
        self.review_decision_label.setStyleSheet(
            f"font-weight: 700; border-radius: 8px; padding: 8px; background: {bg_color}; color: {fg_color};"
        )
        if announce:
            self.statusBar().showMessage(f"已标记人工审核结论：{text}")

    def _set_review_buttons_enabled(self, enabled: bool) -> None:
        self.approve_button.setEnabled(enabled)
        self.reject_button.setEnabled(enabled)
        self.pending_button.setEnabled(enabled)

    def _render_error(self, error: str) -> None:
        self.summary_label.setText("识别失败")
        self._set_audit_status("识别失败", "#fee2e2", "#b91c1c")
        self.audit_metrics_label.setText("命中 0 处文本块 / 0 个链接")
        self.audit_hits_text.setPlainText("")
        self.audit_links_text.setPlainText("")
        self.set_review_decision("未标记", "#f3f4f6", "#111827", announce=False)
        self._set_review_buttons_enabled(False)
        self.statusBar().showMessage("识别失败")
        QMessageBox.critical(self, APP_TITLE, f"识别失败：\n{error}")

    def clear_results(self) -> None:
        self.selected_path = None
        self.current_hit_rows = []
        self.current_links = []
        self.file_label.setText("未选择文件")
        self.summary_label.setText("识别结果会显示在这里")
        self.preview_label.setText("请选择图片")
        self.preview_label.setPixmap(QPixmap())
        self.text_output.clear()
        self.detail_output.clear()
        self.audit_hits_text.clear()
        self.audit_links_text.clear()
        self.audit_metrics_label.setText("命中 0 处文本块 / 0 个链接")
        self._set_audit_status("待识别", "#f3f4f6", "#111827")
        self.set_review_decision("未标记", "#f3f4f6", "#111827", announce=False)
        self._set_review_buttons_enabled(False)
        self.statusBar().showMessage("就绪：请选择一张图片开始识别")


def main() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
