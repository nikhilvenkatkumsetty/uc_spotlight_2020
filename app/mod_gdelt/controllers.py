from arcgis.features import GeoAccessor, GeoSeriesAccessor
from arcgis.geometry import project, intersect
from arcgis import dissolve_boundaries
from arcgis.gis import GIS

from flask import Blueprint, request, jsonify, render_template
from .extractor import Extractor
import traceback
import sqlite3
import time
import os


mod_gdelt = Blueprint('gdelt', __name__, url_prefix='/gdelt', template_folder='gdelt')


def get_gis(cur):

    cur.execute('select esri_url, username, password from config')
    res = cur.fetchone()

    return GIS(*res, verify_cert=False)


def filter_event(event_list):

    if not event_list:
        return False
    else:
        for event in event_list:
            if event['operation'] == 'update':
                return event['id']


def wait_for_service(layer):

    print('Waiting for New Service to Respond')

    tolerance = 6

    while tolerance > 0:
        try:
            props = layer.properties
            if props:
                return props
        except:
            time.sleep(10)
            tolerance -= 1

    return False


def process_hfl(event_layer, gis):

    # Create Name with Time to Avoid Duplicate Errors When Publishing from CSV
    output_name = f'GDELT_Extract_{round(time.time())}'
    csv_out = f'{os.path.dirname(mod_gdelt.root_path)}/scratch/{output_name}.csv'

    try:
        # Wait for Newly Published Service to be Ready
        if not wait_for_service(event_layer):
            raise Exception('Could Not Contact Service That Prompted Route')
        else:
            print(f'Processing: {event_layer.properties.name}')

        # Collect Lastest GDELT Data as a Spatial Data Frame
        gdelt_df = Extractor().get_v2()

        # Dissolve Trigger Event Layer into Single Geometry & Project to Decimal Degrees
        layer_df = dissolve_boundaries(event_layer).query().sdf
        layer_df.SHAPE = project(layer_df.SHAPE.to_list(), '3857', '4326', gis=gis)

        # Determine Intersections
        gdelt_df.SHAPE = intersect('4326', gdelt_df.SHAPE.to_list(), layer_df.SHAPE.to_list()[0])
        gdelt_df['Valid'] = gdelt_df.SHAPE.apply(lambda x: x.get('x') != 'NaN')
        gdelt_df = gdelt_df[gdelt_df['Valid']]

        # Create Name with Time to Avoid Duplicate Errors When Publishing from CSV
        output_name = f'GDELT_Extract_{round(time.time())}'

        # Export Data Frame to Local CSV
        gdelt_df.to_csv(csv_out, index=False)

        # Publish Hosted Feature Layer from CSV
        print('Publishing GDELT Data')
        prp = {'type': 'CSV', 'title': output_name}
        itm = gis.content.add(item_properties=prp, data=csv_out)
        res = itm.publish(publish_parameters={
            'name': f'GDELT_{round(time.time())}',
            'longitudeFieldName': 'ActionGeo_Long',
            'latitudeFieldName': 'ActionGeo_Lat',
            'locationType': 'coordinates',
            'type': 'csv'
        })

        print(f'GDELT Data Published: {res}')
        return res

    finally:
        if os.path.exists(csv_out):
            os.unlink(csv_out)


def is_item_valid(item, con, cur):

    if 'GDELT' not in item.tags:
        return False

    cur.execute('select * from tracking')
    res = [r[0] for r in cur.fetchall()]

    if item.id not in res:
        cur.execute(f"insert into tracking values ('{item.id}')")
        con.commit()
        return True
    else:
        return False


def clear_item_id(item_id, con, cur):

    cur.execute(f"delete from tracking where itemid = '{item_id}'")
    con.commit()


@mod_gdelt.route('/', methods=['GET'])
def index():
    return render_template('gdelt/index.html')


@mod_gdelt.route('/extent', methods=['POST'])
def extent():

    print('Extent Endpoint Triggered')

    # Collect Incoming Event & Item ID
    event = request.get_json()
    event_item_id = filter_event(event.get('events'))
    if not event_item_id:
        print('Trigger Event Was Not an Update')
        return jsonify({'Status': 'Trigger Event Was Not an Update'})

    # Connect to Local Configuration DB
    con = sqlite3.connect(f'{os.path.dirname(mod_gdelt.root_path)}/info.db')
    cur = con.cursor()

    try:
        # Connect to Enterprise & Fetch Item
        gis = get_gis(cur)
        itm = gis.content.get(event_item_id)

        # Check If Item Is Currently Being Processed or Does Not have GDELT Tag
        valid = is_item_valid(itm, con, cur)
        if not valid:
            print(f'Ignoring Item with ID: {itm.id}')
            return jsonify({'Status': f'Ignoring Item with ID: {itm.id}'})

        # We Assume the First Layer Contains the Business Data
        lyr = itm.layers[0]

        # Generate New Feature Layer Based on Input Feature Extent
        hfl_item = process_hfl(lyr, gis)

        # Remove Item from DB
        clear_item_id(event_item_id, con, cur)

        # Return New Item ID
        return jsonify({'ItemID': hfl_item.id, 'Status': 'Success'})

    except:
        clear_item_id(event_item_id, con, cur)
        print(traceback.format_exc())
        return jsonify({'Error': traceback.format_exc(), 'Status': 'Failed'})
