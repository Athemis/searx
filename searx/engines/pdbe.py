"""
 PDBe (Protein Data Bank in Europe)

 @website       https://www.ebi.ac.uk/pdbe
 @provide-api   yes (https://www.ebi.ac.uk/pdbe/api/doc/search.html),
                unlimited
 @using-api     yes
 @results       python dictionary (from json)
 @stable        yes
 @parse         url, title, content, img_src
"""

from json import loads
from flask_babel import gettext
from searx.utils import searx_useragent

categories = ['science']

hide_obsolete = False
hide_unpublished = True

# status codes of unpublished entries
pdb_unpublished_codes = ['HPUB', 'HOLD', 'PROC', 'WAIT', 'AUTH', 'AUCO', 'REPL', 'POLC', 'REFI', 'TRSF', 'WDRN']
# url for api query
pdbe_solr_url = 'https://www.ebi.ac.uk/pdbe/search/pdb/select?'
# base url for results
pdbe_entry_url = 'https://www.ebi.ac.uk/pdbe/entry/pdb/{pdb_id}'
# link to preview image of structure
pdbe_preview_url = 'https://www.ebi.ac.uk/pdbe/static/entry/{pdb_id}_deposited_chain_front_image-200x200.png'


def request(query, params):

    params['url'] = pdbe_solr_url
    params['method'] = 'POST'
    # using searx User-Agent
    params['headers']['User-Agent'] = searx_useragent()
    params['data'] = {
        'q': "{}".format(query),
        'wt': "json"  # request response in parsable format
    }
    return params


def construct_body(result):
    # set title
    title = result['title']

    # construct content body
    content = '{title}&nbsp;<span class="glyphicon glyphicon-user"></span>&nbsp;{authors}'
    content += """&nbsp; \
    <span class="glyphicon glyphicon-book"></span>&nbsp;{journal}&nbsp;<strong>{volume}</strong>&nbsp;{page} \
    <span class="glyphicon glyphicon-calendar"></span>&nbsp; {year}"""

    # replace placeholders with actual content
    try:
        if result['journal']:
            content = content.format(
                title=result['citation_title'],
                authors=result['entry_author_list'][0], journal=result['journal'], volume=result['journal_volume'],
                page=result['journal_page'], year=result['citation_year'])
        else:
            content = content.format(
                title=result['citation_title'],
                authors=result['entry_author_list'][0], journal='', volume='', page='', year=result['release_year'])
        img_src = pdbe_preview_url.format(pdb_id=result['pdb_id'])
    except (KeyError):
        content = None
        img_src = None
        pass

    # construct url for preview image
    try:
        img_src = pdbe_preview_url.format(pdb_id=result['pdb_id'])
    except (KeyError):
        img_src = None
        pass

    return [title, content, img_src]


def response(resp):

    results = []
    json = loads(resp.text)['response']['docs']

    # parse results
    for result in json:
        # reset skip flag
        skip_result = False

        # catch obsolete entries and mark them accordingly
        if result['status'] in pdb_unpublished_codes:
            skip_result = True
        elif result['status'] == 'OBS':
            if not hide_obsolete:
                # expand title to add some sort of warning message
                title = gettext('{title}&nbsp;(OBSOLETE)').format(title=result['title'])
                superseded_url = pdbe_entry_url.format(pdb_id=result['superseded_by'])

                # since we can't construct a proper body from the response, we'll make up our own
                msg_superseded = gettext("This entry has been superseded by")
                content = """<span class="glyphicon glyphicon-exclamation-sign"></span>&nbsp;<em>{msg_superseded} \
                <a href="{url}">{pdb_id}</a></em>""".format(
                    msg_superseded=msg_superseded,
                    url=superseded_url,
                    pdb_id=result['superseded_by'], )

                # obsoleted entries don't have preview images
                img_src = None
            else:
                skip_result = True
        else:
            title, content, img_src = construct_body(result)

        if not skip_result:
            results.append({
                'url': pdbe_entry_url.format(pdb_id=result['pdb_id']),
                'title': title,
                'content': content,
                'img_src': img_src
            })

    return results
