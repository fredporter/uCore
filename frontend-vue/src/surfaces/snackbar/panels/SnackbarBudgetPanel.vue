<template>
  <div class="budget-panel-shell">
    <div class="recipe-header">
      <div class="header-left">
        <span class="material-symbols-outlined header-icon">account_balance_wallet</span>
        <div>
          <h3 class="recipe-title">Sovereign Budget &amp; Resource Policy</h3>
          <p class="recipe-desc">
            Local-first policy enforcement: hard-zero cloud spend invariant.
          </p>
        </div>
      </div>
      <div class="header-meta">
        <span class="recipe-badge">Zero Cloud Spend Policy</span>
      </div>
    </div>

    <!-- USX Card Matrix -->
    <div class="matrix-grid">
      <!-- Remaining -->
      <div class="matrix-card">
        <div class="card-top-row">
          <div class="icon-avatar">
            <span class="material-symbols-outlined">savings</span>
          </div>
          <span class="card-tag">Allowance</span>
        </div>
        <h4 class="card-title">Remaining Budget</h4>
        <p class="card-description">Available allocation for external frontier API fallback requests.</p>
        <div class="card-footer">
          <span class="card-metric">${{ srv.budgetRemaining != null ? srv.budgetRemaining.toFixed(2) : "0.00" }}</span>
          <span class="card-metric-sub">Sovereign free lane</span>
        </div>
      </div>

      <!-- Monthly Cap -->
      <div class="matrix-card">
        <div class="card-top-row">
          <div class="icon-avatar">
            <span class="material-symbols-outlined">credit_card</span>
          </div>
          <span class="card-tag">Cap</span>
        </div>
        <h4 class="card-title">Monthly Limit</h4>
        <p class="card-description">Configured hard budget ceiling per monthly accounting cycle.</p>
        <div class="card-footer">
          <span class="card-metric">${{ srv.budgetLimit.toFixed(2) }}</span>
          <span class="card-metric-sub">Max allowance</span>
        </div>
      </div>

      <!-- Used -->
      <div class="matrix-card">
        <div class="card-top-row">
          <div class="icon-avatar">
            <span class="material-symbols-outlined">receipt_long</span>
          </div>
          <span class="card-tag">Spend</span>
        </div>
        <h4 class="card-title">Recorded Spend</h4>
        <p class="card-description">Total paid cloud API expenditure incurred during this period.</p>
        <div class="card-footer">
          <span class="card-metric" :class="{ 'metric--danger': srv.budgetUsed > 0 }">
            ${{ srv.budgetUsed.toFixed(2) }}
          </span>
          <span class="card-metric-sub">$0.00 Target</span>
        </div>
      </div>

      <!-- Status -->
      <div class="matrix-card">
        <div class="card-top-row">
          <div class="icon-avatar" :class="srv.budgetOverLimit ? 'icon-avatar--danger' : 'icon-avatar--success'">
            <span class="material-symbols-outlined">{{ srv.budgetOverLimit ? 'warning' : 'verified_user' }}</span>
          </div>
          <span class="card-tag" :class="srv.budgetOverLimit ? 'card-tag--danger' : 'card-tag--success'">
            {{ srv.budgetOverLimit ? 'Over Limit' : 'Compliant' }}
          </span>
        </div>
        <h4 class="card-title">Policy Invariant</h4>
        <p class="card-description">Automated gate keeping ecosystem operations completely cost-free.</p>
        <div class="card-footer">
          <span class="status-pill" :class="srv.budgetOverLimit ? 'status-pill--down' : 'status-pill--up'">
            {{ srv.budgetOverLimit ? "OVER LIMIT" : "HARD ZERO OK" }}
          </span>
          <span class="card-metric-sub">Enforced</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useSnackbarOpsStore } from "../../../stores/snackbarOps";

const srv = useSnackbarOpsStore();
</script>

<style scoped>
@import '@udos/usx-tokens/usx-prose.css';

.budget-panel-shell {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  width: 100%;
}

.recipe-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding-bottom: 0.85rem;
  border-bottom: 1px solid var(--usx-color-outline-variant, rgba(255, 255, 255, 0.1));
  flex-wrap: wrap;
  gap: 0.75rem;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.header-icon {
  font-size: 28px;
  color: var(--usx-color-primary, #a8c7fa);
}

.recipe-title {
  margin: 0;
  font-size: 1.15rem;
  font-weight: 600;
  color: var(--usx-color-on-surface, #e2e2e6);
}

.recipe-desc {
  margin: 0.25rem 0 0;
  font-size: 0.82rem;
  color: var(--usx-color-on-surface-variant, #8e9199);
}

.recipe-badge {
  font-size: 0.72rem;
  padding: 0.25rem 0.55rem;
  background: var(--usx-color-surface-container, rgba(255, 255, 255, 0.06));
  border-radius: 4px;
  color: var(--usx-color-on-surface-variant, #c4c6d0);
  font-family: var(--usx-font-family-mono, monospace);
}

.matrix-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(230px, 1fr));
  gap: 1rem;
  width: 100%;
}

.matrix-card {
  display: flex;
  flex-direction: column;
  padding: 1.15rem;
  border-radius: 12px;
  background: var(--usx-color-surface-container, rgba(255, 255, 255, 0.03));
  border: 1px solid var(--usx-color-outline-variant, rgba(255, 255, 255, 0.08));
  transition: transform 0.15s ease, box-shadow 0.15s ease, background 0.15s ease;
}

.matrix-card:hover {
  background: var(--usx-color-surface-container-high, rgba(255, 255, 255, 0.06));
  border-color: var(--usx-color-outline, rgba(255, 255, 255, 0.2));
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
}

.card-top-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.65rem;
}

.icon-avatar {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  background: rgba(168, 199, 250, 0.12);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--usx-color-primary, #a8c7fa);
}

.icon-avatar .material-symbols-outlined {
  font-size: 20px;
}

.icon-avatar--success {
  background: rgba(63, 185, 80, 0.12);
  color: #3fb950;
}

.icon-avatar--danger {
  background: rgba(248, 81, 73, 0.12);
  color: #f85149;
}

.card-tag {
  font-size: 0.68rem;
  padding: 0.18rem 0.45rem;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.06);
  color: var(--usx-color-on-surface-variant, #c4c6d0);
  font-weight: 500;
}

.card-tag--success {
  background: rgba(63, 185, 80, 0.12);
  color: #3fb950;
}

.card-tag--danger {
  background: rgba(248, 81, 73, 0.12);
  color: #f85149;
}

.card-title {
  margin: 0 0 0.3rem;
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--usx-color-on-surface, #e2e2e6);
}

.card-description {
  margin: 0 0 0.85rem;
  font-size: 0.8rem;
  line-height: 1.4;
  color: var(--usx-color-on-surface-variant, #9aa0a6);
  flex: 1;
}

.card-footer {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  padding-top: 0.65rem;
  border-top: 1px solid var(--usx-color-outline-variant, rgba(255, 255, 255, 0.06));
}

.card-metric {
  font-size: 1.25rem;
  font-family: var(--usx-font-family-mono, monospace);
  font-weight: 700;
  color: var(--usx-color-on-surface, #e2e2e6);
}

.metric--danger {
  color: #f85149;
}

.card-metric-sub {
  font-size: 0.72rem;
  color: var(--usx-color-on-surface-variant, #8e9199);
}

.status-pill {
  display: inline-flex;
  align-items: center;
  font-size: 0.68rem;
  font-weight: 600;
  text-transform: uppercase;
  padding: 0.15rem 0.5rem;
  border-radius: 12px;
  letter-spacing: 0.03em;
}

.status-pill--up {
  background: rgba(63, 185, 80, 0.15);
  color: #3fb950;
}

.status-pill--down {
  background: rgba(248, 81, 73, 0.15);
  color: #f85149;
}
</style>
