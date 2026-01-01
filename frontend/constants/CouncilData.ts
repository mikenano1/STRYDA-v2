// app/frontend/constants/CouncilData.ts

export type CouncilType = 'standard' | 'override';

export interface Council {
  id: string;
  name: string;
  type: CouncilType;
  mapUrl?: string; // Optional URL for mandatory override maps
}

// Interface for a Region holding its councils
export interface Region {
  id: string;
  name: string;
  councils: Council[];
}

// THE COMPLETE MASTER LIST OF NZ TERRITORIAL AUTHORITIES
export const NZ_REGIONS: Region[] = [
  {
    id: 'northland',
    name: 'Northland Region',
    councils: [
      { id: 'fndc', name: 'Far North District Council', type: 'standard' },
      { id: 'wdc', name: 'Whangarei District Council', type: 'standard' },
      { id: 'kdc', name: 'Kaipara District Council', type: 'standard' },
    ],
  },
  {
    id: 'auckland',
    name: 'Auckland Region',
    councils: [
      // MANDATORY OVERRIDE: Auckland Unitary Plan
      { id: 'aklc', name: 'Auckland Council', type: 'override', mapUrl: 'https://unitaryplanmaps.aucklandcouncil.govt.nz/upviewer/' },
    ],
  },
  {
    id: 'waikato',
    name: 'Waikato Region',
    councils: [
      { id: 'hamilton', name: 'Hamilton City Council', type: 'standard' },
      { id: 'waikato', name: 'Waikato District Council', type: 'standard' },
      { id: 'thames', name: 'Thames-Coromandel District Council', type: 'standard' },
      { id: 'taupo', name: 'Taupō District Council', type: 'standard' },
      { id: 'matamata', name: 'Matamata-Piako District Council', type: 'standard' },
      { id: 'waipa', name: 'Waipa District Council', type: 'standard' },
      { id: 'southwaikato', name: 'South Waikato District Council', type: 'standard' },
      { id: 'otorohanga', name: 'Ōtorohanga District Council', type: 'standard' },
      { id: 'waitomo', name: 'Waitomo District Council', type: 'standard' },
    ],
  },
  {
    id: 'bay-of-plenty',
    name: 'Bay of Plenty Region',
    councils: [
      // MANDATORY OVERRIDE: Tauranga City Plan Maps
      { id: 'tauranga', name: 'Tauranga City Council', type: 'override', mapUrl: 'https://www.tauranga.govt.nz/council/maps/council-map-viewer-mapi' },
      { id: 'westernbop', name: 'Western Bay of Plenty District Council', type: 'standard' },
      { id: 'whakatane', name: 'Whakatāne District Council', type: 'standard' },
      { id: 'kawerau', name: 'Kawerau District Council', type: 'standard' },
      { id: 'opotiki', name: 'Ōpōtiki District Council', type: 'standard' },
      { id: 'rotorua', name: 'Rotorua Lakes Council', type: 'standard' },
    ],
  },
  {
    id: 'gisborne',
    name: 'Gisborne Region',
    councils: [
      { id: 'gdc', name: 'Gisborne District Council', type: 'standard' },
    ],
  },
  {
    id: 'hawkes-bay',
    name: "Hawke's Bay Region",
    councils: [
      { id: 'napier', name: 'Napier City Council', type: 'standard' },
      { id: 'hastings', name: 'Hastings District Council', type: 'standard' },
      { id: 'wairoa', name: 'Wairoa District Council', type: 'standard' },
      { id: 'chb', name: 'Central Hawke\'s Bay District Council', type: 'standard' },
    ],
  },
  {
    id: 'taranaki',
    name: 'Taranaki Region',
    councils: [
      { id: 'npdc', name: 'New Plymouth District Council', type: 'standard' },
      { id: 'stratford', name: 'Stratford District Council', type: 'standard' },
      { id: 'southtaranaki', name: 'South Taranaki District Council', type: 'standard' },
    ],
  },
  {
    id: 'manawatu-whanganui',
    name: 'Manawatū-Whanganui Region',
    councils: [
      { id: 'pncc', name: 'Palmerston North City Council', type: 'standard' },
      { id: 'whanganui', name: 'Whanganui District Council', type: 'standard' },
      { id: 'manawatu', name: 'Manawatū District Council', type: 'standard' },
      { id: 'rangitikei', name: 'Rangitīkei District Council', type: 'standard' },
      { id: 'tararua', name: 'Tararua District Council', type: 'standard' },
      { id: 'horowhenua', name: 'Horowhenua District Council', type: 'standard' },
      { id: 'ruapehu', name: 'Ruapehu District Council', type: 'standard' },
    ],
  },
  {
    id: 'wellington',
    name: 'Wellington Region',
    councils: [
      // MANDATORY OVERRIDE: WCC Wind Maps
      { id: 'wcc', name: 'Wellington City Council', type: 'override', mapUrl: 'https://wellington.govt.nz/property-rates-and-building/building-and-resource-consents/wind-zones' },
      { id: 'hutt', name: 'Hutt City Council', type: 'standard' },
      { id: 'upperhutt', name: 'Upper Hutt City Council', type: 'standard' },
      { id: 'porirua', name: 'Porirua City Council', type: 'standard' },
      { id: 'kapiti', name: 'Kāpiti Coast District Council', type: 'standard' },
      { id: 'masterton', name: 'Masterton District Council', type: 'standard' },
      { id: 'carterton', name: 'Carterton District Council', type: 'standard' },
      { id: 'southwairarapa', name: 'South Wairarapa District Council', type: 'standard' },
    ],
  },
  {
    id: 'top-of-south',
    name: 'Nelson / Tasman / Marlborough',
    councils: [
      { id: 'nelson', name: 'Nelson City Council', type: 'standard' },
      { id: 'tasman', name: 'Tasman District Council', type: 'standard' },
      { id: 'marlborough', name: 'Marlborough District Council', type: 'standard' },
    ],
  },
  {
    id: 'west-coast',
    name: 'West Coast Region',
    councils: [
      { id: 'buller', name: 'Buller District Council', type: 'standard' },
      { id: 'grey', name: 'Grey District Council', type: 'standard' },
      { id: 'westland', name: 'Westland District Council', type: 'standard' },
    ],
  },
  {
    id: 'canterbury',
    name: 'Canterbury Region',
    councils: [
       // MANDATORY OVERRIDE: Canterbury Maps
      { id: 'ccc', name: 'Christchurch City Council', type: 'override', mapUrl: 'https://mapviewer.canterburymaps.govt.nz/' },
      { id: 'selwyn', name: 'Selwyn District Council', type: 'standard' },
      { id: 'waimakariri', name: 'Waimakariri District Council', type: 'standard' },
      { id: 'ashburton', name: 'Ashburton District Council', type: 'standard' },
      { id: 'timaru', name: 'Timaru District Council', type: 'standard' },
      { id: 'mackenzie', name: 'Mackenzie District Council', type: 'standard' },
      { id: 'waimate', name: 'Waimate District Council', type: 'standard' },
      { id: 'hurunui', name: 'Hurunui District Council', type: 'standard' },
      { id: 'kaikoura', name: 'Kaikōura District Council', type: 'standard' },
    ],
  },
  {
    id: 'otago',
    name: 'Otago Region',
    councils: [
      { id: 'dcc', name: 'Dunedin City Council', type: 'standard' },
      { id: 'qldc', name: 'Queenstown-Lakes District Council', type: 'standard' },
      { id: 'waitaki', name: 'Waitaki District Council', type: 'standard' },
      { id: 'centralotago', name: 'Central Otago District Council', type: 'standard' },
      { id: 'clutha', name: 'Clutha District Council', type: 'standard' },
    ],
  },
  {
    id: 'southland',
    name: 'Southland Region',
    councils: [
      { id: 'icc', name: 'Invercargill City Council', type: 'standard' },
      { id: 'southlanddc', name: 'Southland District Council', type: 'standard' },
      { id: 'gore', name: 'Gore District Council', type: 'standard' },
    ],
  },
];

// Map back to SectionList format for compatibility with existing components
export const NZ_COUNCILS_GROUPED = NZ_REGIONS.map(region => ({
  title: region.name,
  data: region.councils
}));
