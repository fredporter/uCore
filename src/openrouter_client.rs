// uCore/src/openrouter_client.rs

use anyhow::{anyhow, Result};
use reqwest::Client;
use serde::{Deserialize, Serialize};

#[derive(Debug, Deserialize)]
pub struct ChatResponse {
    pub choices: Vec<Choice>,
}
#[derive(Debug, Deserialize)]
pub struct Choice { pub message: Message }
#[derive(Debug, Deserialize)]
pub struct Message { pub content: String }

#[derive(Debug, Serialize)]
pub struct PricingInfo {
    pub model: String,
    pub price_per_1k_input_usd: f64,
    pub price_per_1k_output_usd: f64,
    pub currency: String,
}

pub struct OpenRouterClient {
    pub endpoint: String,
    pub api_key: String,
    client: Client,
}

impl OpenRouterClient {
    pub fn new(api_key: String) -> Self {
        Self {
            endpoint: "https://openrouter.ai/api/v1/chat/completions".to_string(),
            api_key,
            client: Client::new(),
        }
    }

    pub async fn chat(&self, model: &str, system: &str, user: &str) -> Result<String> {
        let payload = serde_json::json!({
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user}
            ]
        });
        let resp = self
            .client
            .post(&self.endpoint)
            .header("Authorization", format!("Bearer {}", self.api_key))
            .json(&payload)
            .send()
            .await?
            .error_for_status()?;
        let chat: ChatResponse = resp.json().await?;
        Ok(chat.choices[0].message.content.clone())
    }

    pub async fn pricing(&self, model: &str) -> Result<PricingInfo> {
        let url = format!("https://openrouter.ai/api/v1/models/{}", model);
        let resp = self
            .client
            .get(&url)
            .header("Authorization", format!("Bearer {}", self.api_key))
            .send()
            .await?
            .error_for_status()?;
        let info: PricingInfo = resp.json().await?;
        Ok(info)
    }

    pub async fn reserve_budget(&self, amount_usd: f64) -> Result<()> {
        // Placeholder: uCore could provide a budgeting endpoint; here we just succeed.
        if amount_usd < 0.0 {
            return Err(anyhow!("Negative budget reservation"));
        }
        Ok(())
    }
}
