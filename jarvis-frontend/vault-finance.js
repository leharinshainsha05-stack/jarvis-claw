export const INITIAL_BALANCES = Object.freeze({
  parentsPaise: 500_000,
  rationPaise: 100_000,
  pocketPaise: 400_000,
});

export function parseRupeesToPaise(value) {
  const match = String(value).trim().match(/^(\d+)(?:\.(\d{1,2}))?$/);
  if (!match) return null;

  const paise = BigInt(match[1]) * 100n + BigInt((match[2] ?? '').padEnd(2, '0') || '0');
  return paise > BigInt(Number.MAX_SAFE_INTEGER) ? null : Number(paise);
}

export function formatINR(paise) {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    minimumFractionDigits: paise % 100 === 0 ? 0 : 2,
    maximumFractionDigits: 2,
  }).format(paise / 100);
}

export function getVaultSummary(balances) {
  return {
    totalPaise: balances.parentsPaise + balances.rationPaise + balances.pocketPaise,
    protectedPaise: balances.parentsPaise,
    reservePaise: balances.rationPaise,
    availablePaise: balances.pocketPaise,
  };
}

export function applyDemoVaultAction(balances, { type, amountPaise, destination }) {
  if (!Number.isSafeInteger(amountPaise) || amountPaise <= 0) {
    return { balances, error: 'Enter an amount greater than zero with up to two decimal places.' };
  }

  if (type === 'add') {
    const pocketPaise = balances.pocketPaise + amountPaise;
    const totalPaise = balances.parentsPaise + balances.rationPaise + pocketPaise;
    if (!Number.isSafeInteger(pocketPaise) || !Number.isSafeInteger(totalPaise)) {
      return { balances, error: 'That amount is too large.' };
    }
    return { balances: { ...balances, pocketPaise }, error: null };
  }

  if (type === 'spend') {
    if (amountPaise > balances.pocketPaise) {
      return { balances, error: 'Exceeds available balance. Protected and reserved funds are not spendable.' };
    }
    return { balances: { ...balances, pocketPaise: balances.pocketPaise - amountPaise }, error: null };
  }

  if (type === 'allocate') {
    if (!['parents', 'ration'].includes(destination)) {
      return { balances, error: 'Choose a valid allocation destination.' };
    }
    if (amountPaise > balances.pocketPaise) {
      return { balances, error: 'Allocation exceeds the available source amount.' };
    }

    const destinationKey = destination === 'parents' ? 'parentsPaise' : 'rationPaise';
    const destinationPaise = balances[destinationKey] + amountPaise;
    if (!Number.isSafeInteger(destinationPaise)) return { balances, error: 'That amount is too large.' };

    return {
      balances: {
        ...balances,
        pocketPaise: balances.pocketPaise - amountPaise,
        [destinationKey]: destinationPaise,
      },
      error: null,
    };
  }

  return { balances, error: 'That demo action is not available.' };
}