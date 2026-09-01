import sys
from pathlib import Path

import pytest

from app.services.nanocoder_acp import NanocoderAcpClient

FAKE_AGENT = r'''import json, os, sys
for line in sys.stdin:
    msg = json.loads(line)
    method = msg.get("method")
    if method == "initialize":
        result = {"protocolVersion": 1, "agentCapabilities": {}}
    elif method == "session/new":
        assert msg["params"]["cwd"] == os.getcwd()
        assert msg["params"]["modeId"] == "plan"
        result = {"sessionId": "session-1"}
    elif method == "session/prompt":
        print(json.dumps({"jsonrpc":"2.0","method":"session/update","params":{"sessionId":"session-1","update":{"sessionUpdate":"agent_message_chunk","content":{"type":"text","text":"planned"}}}}), flush=True)
        print(json.dumps({"jsonrpc":"2.0","id":99,"method":"session/request_permission","params":{"sessionId":"session-1","options":[{"optionId":"allow","kind":"allow_once"}]}}), flush=True)
        permission = json.loads(sys.stdin.readline())
        assert permission["result"]["outcome"]["outcome"] == "cancelled"
        result = {"stopReason": "end_turn"}
    elif method == "session/cancel":
        continue
    else:
        result = {}
    print(json.dumps({"jsonrpc":"2.0","id":msg["id"],"result":result}), flush=True)
'''


def make_client(tmp_path: Path, script: Path, **kwargs) -> NanocoderAcpClient:
    repo = tmp_path / "repos" / "ucore"
    repo.mkdir(parents=True)
    return NanocoderAcpClient(
        [sys.executable, str(script)],
        repository=repo,
        repositories_root=tmp_path / "repos",
        udos_home=tmp_path / "udos",
        dev_mode=True,
        request_timeout=2,
        **kwargs,
    )


@pytest.mark.asyncio
async def test_fake_agent_initialize_session_stream_permission_and_cancel(tmp_path: Path):
    script = tmp_path / "fake_agent.py"
    script.write_text(FAKE_AGENT)
    client = make_client(tmp_path, script)

    async with client:
        initialized = await client.initialize()
        assert initialized["protocolVersion"] == 1
        session_id = await client.new_session()
        result = await client.prompt(session_id, "Plan the reviewed change")
        assert result["stopReason"] == "end_turn"
        event = await client.events.get()
        assert event["method"] == "session/update"
        await client.cancel(session_id)


def test_launch_requires_dev_mode_and_contained_repository(tmp_path: Path):
    root = tmp_path / "repos"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    with pytest.raises(PermissionError, match="Dev Mode"):
        NanocoderAcpClient(
            ["nanocoder", "--acp"],
            repository=outside,
            repositories_root=root,
            udos_home=tmp_path / "udos",
            dev_mode=False,
        )
    with pytest.raises(PermissionError, match="approved root"):
        NanocoderAcpClient(
            ["nanocoder", "--acp"],
            repository=outside,
            repositories_root=root,
            udos_home=tmp_path / "udos",
            dev_mode=True,
        )


def test_provider_policy_is_loopback_only_and_secret_free(tmp_path: Path):
    script = tmp_path / "fake_agent.py"
    script.write_text(FAKE_AGENT)
    client = make_client(tmp_path, script)
    with pytest.raises(PermissionError, match="loopback"):
        client.configure_local_provider(
            name="remote", model="model", base_url="https://provider.example/v1"
        )
    client.configure_local_provider(
        name="ollama", model="mistral:7b", base_url="http://localhost:11434/v1"
    )
    config = (
        tmp_path / "udos/vendor/nanocoder/config/agents.config.json"
    ).read_text()
    assert "mistral:7b" in config
    assert "TOKEN" not in config
    assert "mcpServers" in config
@pytest.mark.asyncio
async def test_invalid_child_output_fails_request_and_closes(tmp_path: Path):
    script = tmp_path / "bad_agent.py"
    script.write_text('print("not-json", flush=True)')
    client = make_client(tmp_path, script)
    with pytest.raises(Exception, match="invalid JSON"):
        await client.initialize()
    await client.close()
