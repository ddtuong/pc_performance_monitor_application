from __future__ import annotations

import tkinter as tk

from models.network import NetworkInterfaceInfo
from models.snapshot import SystemSnapshot
from ui.pages.base import BasePage, unavailable_text
from ui.widgets.chart_card import ChartCard
from ui.widgets.common import set_text
from ui.widgets.info_grid import InfoGrid
from ui.widgets.metric_card import MetricCard
from ui.widgets.table import Column, TableView
from utils.formatters import NA, format_bytes, format_count, format_speed

_DETAIL_KEYS = ["Interface", "Status", "Link speed", "IPv4", "IPv6", "MAC", "Packets received",
                "Packets sent", "Errors (in / out)", "Dropped (in / out)"]


class NetworkPage(BasePage):
    title = "Network"

    def build(self) -> None:
        body = tk.Frame(self, bg=self.p.bg)
        body.pack(fill="both", expand=True, padx=20, pady=16)
        self.sub = self.header(body, "Network", "All interfaces (loopback excluded from totals)")
        row = tk.Frame(body, bg=self.p.bg)
        row.pack(fill="x")
        self.grid_uniform(row, 4)
        self.cards = {}
        for n, (key, title) in enumerate((("down", "Download"), ("up", "Upload"),
                                          ("rx", "Total downloaded"), ("tx", "Total uploaded"))):
            card = MetricCard(row, self.p, title, lines=0, show_bar=False, value_size=16)
            card.grid(row=0, column=n, sticky="nsew", padx=6, pady=6)
            self.cards[key] = card
        self.section(body, "Interfaces")
        self.table = TableView(body, self.p, [
            Column("name", "Interface", 150), Column("st", "Status", 60), Column("ip", "IPv4", 110),
            Column("down", "Download", 90, "e"), Column("up", "Upload", 90, "e"),
            Column("rx", "Received", 85, "e"), Column("tx", "Sent", 85, "e"),
            Column("pr", "Pkts in", 80, "e"), Column("ps", "Pkts out", 80, "e"),
            Column("err", "Errors", 60, "e"), Column("drop", "Dropped", 65, "e")], height=7)
        self.table.pack(fill="x")
        self.table.tree.bind("<<TreeviewSelect>>", lambda _e: self._refresh_detail())
        self.section(body, "Selected interface")
        self.detail = InfoGrid(body, self.p, _DETAIL_KEYS, columns=2)
        self.detail.pack(fill="x")
        self.section(body, "History")
        self.chart = ChartCard(body, self.p, "Download / upload", y_max=None, y_formatter=format_speed,
                               legend=["Download", "Upload"])
        self.chart.pack(fill="both", expand=True)
        self._by_name: dict[str, NetworkInterfaceInfo] = {}

    def _refresh_detail(self) -> None:
        name = self.table.selected() or next(iter(self._by_name), None)
        i = self._by_name.get(name) if name else None
        d = self.detail
        if i is None:
            return
        d.set("Interface", i.name)
        d.set("Status", "Up" if i.is_up else "Down")
        d.set("Link speed", f"{i.speed_mbps} Mbps" if i.speed_mbps else NA)
        d.set("IPv4", ", ".join(i.ipv4) or NA)
        d.set("IPv6", ", ".join(i.ipv6) or NA)
        d.set("MAC", i.mac or NA)
        d.set("Packets received", format_count(i.packets_recv))
        d.set("Packets sent", format_count(i.packets_sent))
        d.set("Errors (in / out)", f"{i.errors_in:,} / {i.errors_out:,}")
        d.set("Dropped (in / out)", f"{i.dropped_in:,} / {i.dropped_out:,}")

    def update_view(self, snap: SystemSnapshot) -> None:
        net = snap.network
        if net is None:
            set_text(self.sub, f"Network information unavailable: {unavailable_text(snap, 'network')}")
            return
        self._by_name = {i.name: i for i in net.interfaces}
        c = self.cards
        c["down"].update_card(format_speed(net.total_download_speed))
        c["up"].update_card(format_speed(net.total_upload_speed))
        c["rx"].update_card(format_bytes(net.total_bytes_recv))
        c["tx"].update_card(format_bytes(net.total_bytes_sent))
        self.table.set_rows([(i.name, (
            i.name, "Up" if i.is_up else "Down", i.ipv4[0] if i.ipv4 else NA,
            format_speed(i.download_speed), format_speed(i.upload_speed),
            format_bytes(i.bytes_recv), format_bytes(i.bytes_sent),
            format_count(i.packets_recv), format_count(i.packets_sent),
            f"{i.errors_in + i.errors_out:,}", f"{i.dropped_in + i.dropped_out:,}")) for i in net.interfaces])
        self._refresh_detail()
        span, cap = self.ctx.axis()
        h = self.ctx.history
        self.chart.draw([h.get("net.down"), h.get("net.up")], span, cap)
