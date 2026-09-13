"""Sovereign Prose Email Compiler.

Compiles bulletproof, single-column HTML emails adhering to USX Prose Standards:
- Strict max-width (580px/640px)
- MSO table fallbacks for Outlook compatibility
- System typography stacks (Charter serif, Inter sans)
- Embedded hero GIF (via CID or link)
- Zero tracking pixels and zero third-party web font downloads
"""
from __future__ import annotations

import html
from typing import Optional


def compile_prose_email(
    title: str,
    lead_text: str,
    body_html: str,
    action_label: Optional[str] = None,
    action_url: Optional[str] = None,
    hero_gif_src: Optional[str] = None,
    theme: str = "dark",
) -> str:
    """Compile a single-column, bulletproof HTML email."""
    safe_title = html.escape(title)
    safe_lead = html.escape(lead_text)

    # Color tokens based on USX dark or light theme
    if theme == "light":
        bg_color = "#F6F8FA"
        card_bg = "#FFFFFF"
        text_primary = "#1F2328"
        text_muted = "#656D76"
        border_color = "#D0D7DE"
        btn_bg = "#0969DA"
        btn_text = "#FFFFFF"
    else:
        bg_color = "#0D1117"
        card_bg = "#161B22"
        text_primary = "#E6EDF3"
        text_muted = "#8B949E"
        border_color = "#30363D"
        btn_bg = "#58A6FF"
        btn_text = "#0D1117"

    hero_block = ""
    if hero_gif_src:
        hero_block = f"""
        <tr>
          <td align="center" style="padding: 24px 24px 16px 24px;">
            <img src="{hero_gif_src}" alt="Hero Animation" width="128" height="128" style="display: block; border: 0; outline: none; text-decoration: none; border-radius: 6px; max-width: 100%; height: auto;" />
          </td>
        </tr>
        """

    button_block = ""
    if action_label and action_url:
        safe_action_label = html.escape(action_label)
        button_block = f"""
        <tr>
          <td align="center" style="padding: 24px 24px 32px 24px;">
            <!--[if mso]>
            <v:roundrect xmlns:v="urn:schemas-microsoft-com:vml" xmlns:w="urn:schemas-microsoft-com:office:word" href="{action_url}" style="height:48px;v-text-anchor:middle;width:240px;" arcsize="10%" strokecolor="{btn_bg}" fillcolor="{btn_bg}">
            <w:anchorlock/>
            <center style="color:{btn_text};font-family:sans-serif;font-size:16px;font-weight:bold;">{safe_action_label}</center>
            </v:roundrect>
            <![endif]-->
            <!--[if !mso]><!-->
            <a href="{action_url}" target="_blank" style="background-color: {btn_bg}; color: {btn_text}; display: inline-block; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size: 16px; font-weight: 600; line-height: 48px; text-align: center; text-decoration: none; width: 240px; border-radius: 4px; -webkit-text-size-adjust: none;">{safe_action_label}</a>
            <!--<![endif]-->
          </td>
        </tr>
        """

    return f"""<!DOCTYPE html>
<html lang="en" xmlns="http://www.w3.org/1999/xhtml" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:o="urn:schemas-microsoft-com:office:office">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta http-equiv="X-UA-Compatible" content="IE=edge">
  <meta name="x-apple-disable-message-reformatting">
  <title>{safe_title}</title>
  <!--[if mso]>
  <noscript>
    <xml>
      <o:OfficeDocumentSettings>
        <o:PixelsPerInch>96</o:PixelsPerInch>
      </o:OfficeDocumentSettings>
    </xml>
  </noscript>
  <![endif]-->
  <style>
    body {{ margin: 0; padding: 0; width: 100% !important; -webkit-text-size-adjust: 100%; -ms-text-size-adjust: 100%; }}
    img {{ border: 0; outline: none; text-decoration: none; -ms-interpolation-mode: bicubic; }}
    table {{ border-collapse: collapse; mso-table-lspace: 0pt; mso-table-rspace: 0pt; }}
  </style>
</head>
<body style="margin: 0; padding: 0; background-color: {bg_color}; font-family: Charter, 'Bitstream Charter', 'Sitka Text', Cambria, Georgia, serif;">
  <div style="background-color: {bg_color}; padding: 32px 16px;">
    <!--[if mso]>
    <table align="center" border="0" cellpadding="0" cellspacing="0" width="600">
    <tr>
    <td>
    <![endif]-->
    <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 600px; background-color: {card_bg}; border: 1px solid {border_color}; border-radius: 8px; overflow: hidden; margin: 0 auto;">
      {hero_block}
      <tr>
        <td style="padding: 16px 32px 8px 32px; text-align: center;">
          <h1 style="margin: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; font-size: 26px; font-weight: 700; line-height: 1.3; color: {text_primary};">{safe_title}</h1>
        </td>
      </tr>
      <tr>
        <td style="padding: 8px 32px 16px 32px; text-align: center;">
          <p style="margin: 0; font-size: 18px; line-height: 1.5; color: {text_muted};">{safe_lead}</p>
        </td>
      </tr>
      <tr>
        <td style="padding: 16px 32px; color: {text_primary}; font-size: 16px; line-height: 1.65;">
          {body_html}
        </td>
      </tr>
      {button_block}
      <tr>
        <td style="padding: 16px 32px 24px 32px; border-top: 1px solid {border_color}; text-align: center;">
          <p style="margin: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; font-size: 12px; line-height: 1.4; color: {text_muted};">
            Dispatched via sovereign uDos • Zero tracking pixels • Local first
          </p>
        </td>
      </tr>
    </table>
    <!--[if mso]>
    </td>
    </tr>
    </table>
    <![endif]-->
  </div>
</body>
</html>"""


def generate_plain_text_email(
    title: str,
    lead_text: str,
    body_text: str,
    action_label: Optional[str] = None,
    action_url: Optional[str] = None,
) -> str:
    """Generate a clean plain-text fallback version."""
    lines = [
        title,
        "=" * len(title),
        "",
        lead_text,
        "",
        body_text,
        "",
    ]
    if action_label and action_url:
        lines.extend([f"-> {action_label}: {action_url}", ""])
    lines.append("Dispatched via sovereign uDos (offline-first, zero tracking)")
    return "\n".join(lines)
