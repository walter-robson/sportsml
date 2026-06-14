// NBA player ID → display surname. Mirrors scripts/seed_synthetic_data.py's
// roster snapshots so the synthetic-data demo path renders real names.
// In production this lookup will come from the Players Object Type, not a constant.

export const PLAYER_NAMES: Readonly<Record<string, string>> = {
  // BOS
  '1628369': 'Tatum',
  '1627759': 'Brown',
  '201950': 'Holiday',
  '1628401': 'White',
  '204001': 'Porzingis',
  '1630202': 'Pritchard',
  '201143': 'Horford',
  '1630573': 'Hauser',
  '1628378': 'Kornet',
  '1629057': 'Brissett',
  // GSW
  '201939': 'Curry',
  '2738': 'Thompson',
  '203952': 'Wiggins',
  '203110': 'Green',
  '1626172': 'Looney',
  '1628395': 'Kuminga',
  '1628384': 'Moody',
  '1630228': 'Podziemski',
  '1641706': 'TJD',
  '1630225': 'Hield',
  // LAL
  '2544': 'James',
  '203076': 'Davis',
  '1627833': 'Reaves',
  '1626156': 'Russell',
  '203497': 'Hachimura',
  '1630559': 'Vincent',
  '203944': 'Wood',
  '1630224': 'Hayes',
  '1629680': 'LeVert',
  // DEN
  '203999': 'Jokic',
  '1627750': 'Murray',
  '1628960': 'MPJ',
  '203914': 'KCP',
  '1630168': 'Gordon',
  '1630174': 'Strawther',
  '1629019': 'Braun',
  '1630268': 'Watson',
  // OKC
  '1628983': 'SGA',
  '1628973': 'Dort',
  '1629029': 'Giddey',
  '1641705': 'Holmgren',
  '1630167': 'JWilliams',
  '1641709': 'Joe',
  '1630244': 'Wiggins',
  '1630238': 'Wallace',
  '1628988': 'Caruso',
  '1641710': 'Mann',
  // MIL
  '203507': 'Antetokounmpo',
  '201142': 'Lillard',
  '1628978': 'Lopez',
  '203114': 'Middleton',
  '1630193': 'Beauchamp',
  '1641754': 'Sims',
  '204022': 'Crowder',
  '203501': 'Connaughton',
};

export function nameFor(playerId: string): string {
  return PLAYER_NAMES[playerId] ?? `#${playerId}`;
}
