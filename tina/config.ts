import { defineConfig, type Collection, type TinaField } from 'tinacms';

const branch = process.env.GITHUB_BRANCH || process.env.HEAD || 'main';

const text = (name: string, label: string, required = true): TinaField => ({ type: 'string', name, label, required });
const image = (name: string, label: string): TinaField => ({ type: 'image', name, label });
const timeFields: TinaField[] = [text('day', 'Day'), text('time', 'Time')];
const scheduleFields: TinaField[] = [
  text('title', 'Gathering name'),
  { type: 'object', name: 'times', label: 'Days and times', list: true, ui: { itemProps: (item) => ({ label: `${item?.day || 'Day'} · ${item?.time || 'Time'}` }) }, fields: timeFields },
  text('note', 'Short description'),
];

const home: Collection = {
  name: 'home', label: 'Home page', path: 'content', format: 'json', match: { include: 'home' },
  ui: { router: () => '/' },
  fields: [
    { type: 'object', name: 'hero', label: 'Top welcome section', fields: [text('heading_intro', 'Opening words'), text('heading_highlight', 'Church name'), text('text', 'Welcome text'), text('service_time', 'Sunday service time'), text('location', 'Meeting location'), image('image', 'Background photo'), text('image_alt', 'Photo description')] },
    { type: 'object', name: 'who', label: 'Who we are', fields: [text('eyebrow', 'Small heading'), text('heading', 'Main heading'), text('text', 'Description')] },
    { type: 'object', name: 'believe', label: 'What we believe', fields: [text('eyebrow', 'Small heading'), text('heading', 'Main heading'), { type: 'string', name: 'body', label: 'Text', ui: { component: 'textarea' } }, image('image', 'Photo'), text('image_alt', 'Photo description')] },
    { type: 'object', name: 'gatherings', label: 'Weekly gatherings', fields: [text('eyebrow', 'Small heading'), text('heading', 'Main heading'), { type: 'object', name: 'cards', label: 'Gatherings', list: true, ui: { itemProps: (item) => ({ label: item?.title || 'Gathering' }) }, fields: scheduleFields }, { type: 'string', name: 'footer_note', label: 'Note below the gatherings', ui: { component: 'textarea' } }] },
    { type: 'object', name: 'life', label: 'Our church life', fields: [text('eyebrow', 'Small heading'), text('heading', 'Main heading'), { type: 'object', name: 'columns', label: 'Three short descriptions', list: true, ui: { itemProps: (item) => ({ label: item?.heading || 'Description' }) }, fields: [text('heading', 'Heading'), { type: 'string', name: 'text', label: 'Text', ui: { component: 'textarea' } }] }, { type: 'string', name: 'body', label: 'Longer description', ui: { component: 'textarea' } }] },
    { type: 'object', name: 'gallery', label: 'Photo gallery', fields: [text('eyebrow', 'Small heading'), text('heading', 'Main heading'), { type: 'object', name: 'photos', label: 'Photos', list: true, ui: { itemProps: (item) => ({ label: item?.alt || 'Photo' }) }, fields: [image('image', 'Photo'), text('alt', 'Photo description')] }] },
    { type: 'object', name: 'cta', label: 'Closing invitation', fields: [text('heading', 'Heading'), { type: 'string', name: 'text', label: 'Invitation text', ui: { component: 'textarea' } }] },
  ],
};

const messages: Collection = {
  name: 'messages', label: 'Sunday Messages page', path: 'content', format: 'json', match: { include: 'messages' },
  ui: { router: () => '/messages/' },
  fields: [text('eyebrow', 'Small heading'), text('title', 'Page heading'), { type: 'string', name: 'intro', label: 'Introduction', ui: { component: 'textarea' } }, text('youtube_channel', 'YouTube channel link'), { type: 'object', name: 'videos', label: 'Videos', list: true, ui: { itemProps: (item) => ({ label: item?.title || 'Sunday message' }) }, fields: [text('title', 'Video title'), text('youtube', 'YouTube link')] }, text('cta_heading', 'Closing heading'), { type: 'string', name: 'cta_text', label: 'Closing text', ui: { component: 'textarea' } }],
};

const faith: Collection = {
  name: 'faith', label: 'Statement of Faith page', path: 'content', format: 'json', match: { include: 'statement-of-faith' },
  ui: { router: () => '/statement-of-faith/' },
  fields: [text('eyebrow', 'Small heading'), text('title', 'Page heading'), { type: 'string', name: 'intro', label: 'Introduction', ui: { component: 'textarea' } }, { type: 'object', name: 'points', label: 'Faith points', list: true, ui: { itemProps: (item) => ({ label: item?.heading || 'Faith point' }) }, fields: [text('heading', 'Heading'), { type: 'string', name: 'text', label: 'Statement', ui: { component: 'textarea' } }] }, text('cta_heading', 'Closing heading'), { type: 'string', name: 'cta_text', label: 'Closing text', ui: { component: 'textarea' } }],
};

const contact: Collection = {
  name: 'contact', label: 'Contact and schedule page', path: 'content', format: 'json', match: { include: 'contact' },
  ui: { router: () => '/contact/' },
  fields: [text('eyebrow', 'Small heading'), text('title', 'Page heading'), { type: 'string', name: 'intro', label: 'Introduction', ui: { component: 'textarea' } }, text('schedule_eyebrow', 'Schedule small heading'), text('schedule_heading', 'Schedule heading'), { type: 'object', name: 'schedule', label: 'Weekly schedule', list: true, ui: { itemProps: (item) => ({ label: item?.title || 'Gathering' }) }, fields: scheduleFields }, text('email', 'Contact email'), text('meeting_place', 'Meeting place'), { type: 'string', name: 'meeting_note', label: 'Directions note', ui: { component: 'textarea' } }, text('sunday_service', 'Sunday service details'), text('cta_heading', 'Closing heading'), { type: 'string', name: 'cta_text', label: 'Closing text', ui: { component: 'textarea' } }],
};

const site: Collection = {
  name: 'site', label: 'Site-wide settings', path: 'content', format: 'json', match: { include: 'site' },
  ui: { global: true },
  fields: [text('church_name', 'Church name'), text('email', 'Contact email'), { type: 'string', name: 'footer_blurb', label: 'Footer description', ui: { component: 'textarea' } }, text('meeting_place', 'Meeting place'), text('service_time', 'Sunday service time'), text('footer_tagline', 'Footer closing line'), text('youtube', 'YouTube link'), text('instagram', 'Instagram link'), text('facebook', 'Facebook link')],
};

const pageSections: TinaField = {
  type: 'object', name: 'sections', label: 'Page sections', list: true,
  ui: { visualSelector: true, itemProps: (item) => ({ label: item?.heading || item?.title || 'Page section' }) },
  templates: [
    { name: 'text', label: 'Text', fields: [text('heading', 'Heading', false), { type: 'string', name: 'body', label: 'Text', ui: { component: 'textarea' } }, { type: 'boolean', name: 'shaded', label: 'Use a light background' }] },
    { name: 'image_text', label: 'Photo with text', fields: [text('heading', 'Heading', false), { type: 'string', name: 'body', label: 'Text', ui: { component: 'textarea' } }, image('image', 'Photo'), text('image_alt', 'Photo description'), { type: 'string', name: 'image_side', label: 'Photo position', options: [{ value: 'left', label: 'Left' }, { value: 'right', label: 'Right' }] }, { type: 'boolean', name: 'shaded', label: 'Use a light background' }] },
    { name: 'columns', label: 'Columns', fields: [text('heading', 'Heading', false), { type: 'object', name: 'columns', label: 'Columns', list: true, fields: [text('heading', 'Column heading'), { type: 'string', name: 'text', label: 'Column text', ui: { component: 'textarea' } }] }, { type: 'boolean', name: 'shaded', label: 'Use a light background' }] },
    { name: 'video', label: 'YouTube video', fields: [text('title', 'Video title'), text('youtube', 'YouTube link'), { type: 'boolean', name: 'shaded', label: 'Use a light background' }] },
    { name: 'cta', label: 'Invitation banner', fields: [text('heading', 'Heading', false), { type: 'string', name: 'text', label: 'Invitation text', ui: { component: 'textarea' } }, text('button_label', 'Button words'), text('button_link', 'Button link')] },
  ],
};

const pages: Collection = {
  name: 'pages', label: 'Other pages', path: 'content/pages', format: 'json',
  ui: { router: ({ document }) => `/${document._sys.filename}/`, filename: { slugify: (values) => values?.title?.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '') || 'new-page' } },
  fields: [text('title', 'Page title'), { type: 'string', name: 'description', label: 'Search and sharing description', ui: { component: 'textarea' } }, text('eyebrow', 'Small heading', false), { type: 'string', name: 'intro', label: 'Introduction', ui: { component: 'textarea' } }, { type: 'boolean', name: 'show_in_menu', label: 'Show this page in the top menu' }, text('menu_label', 'Words shown in the top menu', false), { type: 'number', name: 'menu_order', label: 'Menu position' }, { type: 'boolean', name: 'published', label: 'Publish this page' }, pageSections],
};

export default defineConfig({
  branch,
  clientId: process.env.TINA_CLIENT_ID,
  token: process.env.TINA_TOKEN,
  build: { outputFolder: 'admin', publicFolder: 'public' },
  media: { tina: { mediaRoot: 'assets/img', publicFolder: 'public' } },
  schema: { collections: [home, messages, faith, contact, site, pages] },
});
