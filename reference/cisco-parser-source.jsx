import React, { useState } from "react";
import {
  Upload,
  FileJson,
  Copy,
  Download,
  CheckCircle,
  RotateCcw,
} from "lucide-react";

function parseCiscoConfig(text) {
  const lines = text.split(/\r?\n/);

  const result = {
    vendor: "Cisco",
    hostname: null,
    management_access: {
      ssh_enabled: false,
      telnet_enabled: false,
      http_enabled: false,
      https_enabled: false,
    },
    authentication: {
      local_login: false,
      password_encryption: false,
      enable_secret_configured: false,
      users: [],
    },
    interfaces: [],
    access_lists: [],
    logging: {},
    other_security_settings: [],
  };

  let currentInterface = null;
  let currentVty = false;

  for (let line of lines) {
    const trimmed = line.trim();

    if (!trimmed || trimmed.startsWith("!")) continue;

    // Hostname
    if (trimmed.startsWith("hostname ")) {
      result.hostname = trimmed.substring(9).trim();
    }

    // SSH
    if (trimmed.includes("transport input") && trimmed.includes("ssh")) {
      result.management_access.ssh_enabled = true;
    }

    // Telnet
    if (trimmed.includes("transport input") && trimmed.includes("telnet")) {
      result.management_access.telnet_enabled = true;
    }

    // HTTP
    if (trimmed === "ip http server") {
      result.management_access.http_enabled = true;
    }

    if (trimmed === "no ip http server") {
      result.management_access.http_enabled = false;
    }

    // HTTPS
    if (trimmed === "ip http secure-server") {
      result.management_access.https_enabled = true;
    }

    if (trimmed === "no ip http secure-server") {
      result.management_access.https_enabled = false;
    }

    // Authentication
    if (trimmed === "login local") {
      result.authentication.local_login = true;
    }

    if (trimmed === "service password-encryption") {
      result.authentication.password_encryption = true;
    }

    if (trimmed.startsWith("enable secret")) {
      result.authentication.enable_secret_configured = true;
    }

    // Users
    if (trimmed.startsWith("username ")) {
      const match = trimmed.match(
        /^username\s+(\S+)\s+privilege\s+(\d+)/
      );

      if (match) {
        result.authentication.users.push({
          username: match[1],
          privilege: match[2],
        });
      }
    }

    // Interfaces
    if (trimmed.startsWith("interface ")) {
      if (currentInterface) {
        result.interfaces.push(currentInterface);
      }

      currentInterface = {
        name: trimmed.substring(10).trim(),
      };
      currentVty = false;
      continue;
    }

    if (currentInterface) {
      if (trimmed.startsWith("description ")) {
        currentInterface.description =
          trimmed.substring(12).trim();
      }

      if (trimmed.startsWith("ip address ")) {
        const parts = trimmed.split(/\s+/);

        if (parts.length >= 4) {
          currentInterface.ip_address = parts[2];
          currentInterface.subnet_mask = parts[3];
        }
      }

      if (trimmed === "shutdown") {
        currentInterface.admin_status = "down";
      }

      if (trimmed === "no shutdown") {
        currentInterface.admin_status = "up";
      }
    }

    // VTY
    if (trimmed.startsWith("line vty")) {
      currentVty = true;
      currentInterface = null;
    }

    if (currentVty && trimmed.includes("transport input")) {
      result.vty_transport = trimmed
        .replace("transport input", "")
        .trim();
    }

    // ACL
    if (
      trimmed.startsWith("access-list") ||
      trimmed.startsWith("ip access-list")
    ) {
      result.access_lists.push(trimmed);
    }

    // Logging
    if (trimmed.startsWith("logging ")) {
      if (!result.logging.settings) {
        result.logging.settings = [];
      }

      result.logging.settings.push(trimmed);
    }

    // Other security settings
    if (
      trimmed.includes("crypto key generate") ||
      trimmed.includes("no ip http") ||
      trimmed.includes("snmp-server") ||
      trimmed.includes("aaa ") ||
      trimmed.includes("login block-for")
    ) {
      result.other_security_settings.push(trimmed);
    }
  }

  if (currentInterface) {
    result.interfaces.push(currentInterface);
  }

  // Remove empty values
  if (!result.hostname) delete result.hostname;

  if (result.authentication.users.length === 0) {
    delete result.authentication.users;
  }

  if (
    result.other_security_settings.length === 0
  ) {
    delete result.other_security_settings;
  }

  if (
    result.access_lists.length === 0
  ) {
    delete result.access_lists;
  }

  if (
    result.interfaces.length === 0
  ) {
    delete result.interfaces;
  }

  if (
    result.logging.settings?.length === 0
  ) {
    delete result.logging.settings;
  }

  return result;
}

export default function App() {
  const [file, setFile] = useState(null);
  const [rawConfig, setRawConfig] = useState("");
  const [jsonOutput, setJsonOutput] = useState(null);
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleFile = (selectedFile) => {
    if (!selectedFile) return;

    setFile(selectedFile);

    const reader = new FileReader();

    reader.onload = (event) => {
      setRawConfig(event.target.result);
    };

    reader.readAsText(selectedFile);
  };

  const convertConfig = () => {
    if (!rawConfig) return;

    setLoading(true);

    setTimeout(() => {
      const parsed = parseCiscoConfig(rawConfig);

      setJsonOutput(parsed);
      setLoading(false);
    }, 800);
  };

  const copyJSON = async () => {
    if (!jsonOutput) return;

    await navigator.clipboard.writeText(
      JSON.stringify(jsonOutput, null, 2)
    );

    setCopied(true);

    setTimeout(() => {
      setCopied(false);
    }, 1500);
  };

  const downloadJSON = () => {
    if (!jsonOutput) return;

    const blob = new Blob(
      [JSON.stringify(jsonOutput, null, 2)],
      { type: "application/json" }
    );

    const url = URL.createObjectURL(blob);

    const a = document.createElement("a");
    a.href = url;
    a.download = "config.json";
    a.click();

    URL.revokeObjectURL(url);
  };

  const reset = () => {
    setFile(null);
    setRawConfig("");
    setJsonOutput(null);
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "#f5f7fb",
        padding: "40px",
        fontFamily: "Arial, sans-serif",
      }}
    >
      <div
        style={{
          maxWidth: "1000px",
          margin: "auto",
        }}
      >
        <h1>
          Cisco Configuration Parser
        </h1>

        <p style={{ color: "#666" }}>
          Convert Cisco configuration files into
          structured JSON.
        </p>

        <div
          style={{
            background: "white",
            padding: "30px",
            borderRadius: "15px",
            marginTop: "25px",
            border: "1px solid #ddd",
          }}
        >
          <label
            style={{
              display: "block",
              border: "2px dashed #aaa",
              padding: "40px",
              textAlign: "center",
              cursor: "pointer",
              borderRadius: "12px",
            }}
          >
            <Upload size={40} />

            <h3>
              {file
                ? file.name
                : "Upload Cisco Configuration"}
            </h3>

            <p>
              Select a .txt, .cfg or .conf file
            </p>

            <input
              type="file"
              accept=".txt,.cfg,.conf"
              style={{ display: "none" }}
              onChange={(e) =>
                handleFile(e.target.files[0])
              }
            />
          </label>

          {file && (
            <div style={{ marginTop: "20px" }}>
              <CheckCircle size={18} />

              <span style={{ marginLeft: "8px" }}>
                Configuration loaded successfully
              </span>
            </div>
          )}

          <button
            onClick={convertConfig}
            disabled={!file || loading}
            style={{
              marginTop: "25px",
              padding: "12px 25px",
              border: "none",
              borderRadius: "8px",
              cursor: "pointer",
              background: "#111",
              color: "white",
            }}
          >
            {loading
              ? "Parsing Configuration..."
              : "Convert to JSON"}
          </button>
        </div>

        {jsonOutput && (
          <div
            style={{
              background: "white",
              padding: "30px",
              borderRadius: "15px",
              marginTop: "25px",
              border: "1px solid #ddd",
            }}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
              }}
            >
              <h2>
                <FileJson size={22} />
                {" "}Structured Configuration
              </h2>

              <div>
                <button
                  onClick={copyJSON}
                  style={{
                    marginRight: "10px",
                    padding: "10px",
                  }}
                >
                  <Copy size={16} />

                  {copied
                    ? " Copied"
                    : " Copy"}
                </button>

                <button
                  onClick={downloadJSON}
                  style={{
                    padding: "10px",
                  }}
                >
                  <Download size={16} />
                  {" "}Download JSON
                </button>
              </div>
            </div>

            <pre
              style={{
                background: "#111",
                color: "#eee",
                padding: "20px",
                borderRadius: "10px",
                overflowX: "auto",
                marginTop: "20px",
              }}
            >
              {JSON.stringify(
                jsonOutput,
                null,
                2
              )}
            </pre>

            <button
              onClick={reset}
              style={{
                marginTop: "20px",
                padding: "10px 15px",
              }}
            >
              <RotateCcw size={16} />
              {" "}Reset
            </button>
          </div>
        )}
      </div>
    </div>
  );
}