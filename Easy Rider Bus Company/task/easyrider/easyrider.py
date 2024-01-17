from datetime import datetime
import json
import re

class EasyRider:
    json_string = None
    json = None
    fields_validation_definition = {
        'bus_id': {'required': True, 'type': 'int', 'format': '[0-9]*', 'nb_of_missing_values': 0, 'nb_of_wrong_data_type': 0},
        'stop_id': {'required': True, 'type': 'int', 'format': '[0-9]*','nb_of_missing_values': 0, 'nb_of_wrong_data_type': 0},
        'stop_name': {'required': True, 'type': 'str', 'format': '^([A-Z]{1}[a-zA-Z]*\s+)+(Road|Avenue|Boulevard|Street)$','nb_of_missing_values': 0, 'nb_of_wrong_data_type': 0},
        'next_stop': {'required': True, 'type': 'int', 'format': '[0-9]*','nb_of_missing_values': 0, 'nb_of_wrong_data_type': 0},
        'stop_type': {'required': False, 'type': 'str', 'format': '^(S|F|O)$','nb_of_missing_values': 0, 'nb_of_wrong_data_type': 0},
        'a_time': {'required': True, 'type': 'str', 'format': '^[0-2]{1}[0-9]{1}:[0-5]{1}[0-9]{1}$','nb_of_missing_values': 0, 'nb_of_wrong_data_type': 0}
    }

    def __init__(self, json_string):
        self.json_string = json_string
        self.json = json.loads(json_string)


    def validate_fields(self):
        for field in self.json:
            for key in self.fields_validation_definition.keys():
                if key in ['stop_name', 'stop_type', 'a_time']:
                    self.validate_mandatory_fields(key, field[key])
                    self.validate_data_type_fields(key, field[key])

    def validate_mandatory_fields(self, field_name, field_value):
        if self.fields_validation_definition[field_name]['required']:
            if field_value is None or len(str(field_value)) == 0:
                self.fields_validation_definition[field_name]['nb_of_missing_values'] += 1

    def validate_data_type_fields(self, field_name, field_value):
        if (len(str(field_value)) != 0
                #and (type(field_value).__name__ != self.fields_validation_definition[field_name]['type']
                #    )
            and not re.match(self.fields_validation_definition[field_name]['format'], str(field_value))
        ):
            self.fields_validation_definition[field_name]['nb_of_wrong_data_type'] += 1

    def print_results(self):
        nb_of_errors = 0
        result = []
        for key in self.fields_validation_definition.keys():
            if key in ['stop_name', 'stop_type', 'a_time']:
                nb_of_errors += (self.fields_validation_definition[key]['nb_of_missing_values']
                                 + self.fields_validation_definition[key]['nb_of_wrong_data_type'])
                result.append({key: self.fields_validation_definition[key]['nb_of_missing_values']
                                    + self.fields_validation_definition[key]['nb_of_wrong_data_type']})

        print(f"Type and required field validation: {nb_of_errors} errors")
        print('\n'.join([f"{key}: {value}" for d in result for key, value in d.items()]))

    def print_line_names_and_number_of_stops(self):
        line_names_and_stops = {}
        for field in self.json:
            if len(str(field['bus_id'])) != 0:
                bus_id = int(str(field['bus_id']).strip())
                if bus_id in line_names_and_stops.keys():
                    line_names_and_stops.update({bus_id: line_names_and_stops[bus_id] +1 })
                else :
                    line_names_and_stops.update({bus_id: 1})

        print(f"Line names and number of stops:")
        print('\n'.join([f"{key}: {value}" for key, value in line_names_and_stops.items()]))

    def get_distinct_bus_lines(self):
        return set(item["bus_id"] for item in self.json)

    def check_if_start_end_in_bus_line_exists(self, bus_id):
        result = {}
        for item in self.json:
            if item["bus_id"] == bus_id:
                if len(str(item["stop_type"])) != 0:
                    if not result:
                        result = {item['stop_type']: 1}
                    elif item["stop_type"] in result:
                        result.update({item["stop_type"]: result[item['stop_type']] + 1})
                    else:
                        result.update({item["stop_type"]: 1})

        if 'S' not in list(result.keys()) or 'F' not in list(result.keys()) :
            return False
        elif result['S'] == 1 and result['F'] == 1:
            return True
        else:
            return False


    def print_all_stops(self):
        start_stops = []
        finish_stops = []
        transfer_stops = []
        for item in self.json:
            if sum(1 for a in self.json if "stop_name" in a and a["stop_name"] == item["stop_name"]) > 1:
                transfer_stops.append(item["stop_name"])

            if item["stop_type"] == 'S':
                start_stops.append(item["stop_name"])
            if item["stop_type"] == 'F':
                finish_stops.append(item["stop_name"])

        print(f"Start stops: {len(list(set(start_stops)))} {sorted(list(set(start_stops)))}")
        print(f"Transfer stops: {len(list(set(transfer_stops)))} {sorted(list(set(transfer_stops)))}")
        print(f"Finish stops: {len(list(set(finish_stops)))} {sorted(list(set(finish_stops)))}")


    def check_timetable(self):
        time_format = "%H:%M"
        print("Arrival time test:")
        current_time = {}
        result = True
        for bus in self.get_distinct_bus_lines():
            for item in self.json:
                if item["bus_id"] == bus:
                    if not current_time:
                        current_time = {item["bus_id"]: datetime.strptime(item["a_time"],time_format).time()}
                    elif item["bus_id"] not in current_time:
                        current_time = {item["bus_id"]: datetime.strptime(item["a_time"], time_format).time()}
                    elif datetime.strptime(item["a_time"],time_format).time() <= current_time[item["bus_id"]]:
                        print(f"bus_id line {item['bus_id']}: wrong time on station {item['stop_name']}")
                        result = False
                        break
                    else:
                        current_time = {item["bus_id"]: datetime.strptime(item["a_time"], time_format).time()}


        if result:
            print("OK")

    def get_transfer_stops(self):
        transfer_stops = []
        for item in self.json:
            if sum(1 for a in self.json if "stop_name" in a and a["stop_name"] == item["stop_name"] and (a["stop_type"] == "O" or a["stop_type"] == "")) > 1:
                transfer_stops.append(item["stop_name"])

        return set(transfer_stops)

    def check_on_demands_stop(self):
        print("On demand stops test:")
        on_demands_stops = []
        result = True
        for item in self.json:
            if item["stop_type"] == "O":
                on_demands_stops.append(item["stop_name"])
                result = False

        common = set(on_demands_stops).intersection(self.get_transfer_stops())

        print(set(on_demands_stops))
        print(self.get_transfer_stops())
        print(common)


        if len(common) == 0:
            print("Wrong stop type: OK")
        else:
            print(f"Wrong stop type: {sorted(list(set(common)))}")


if __name__ == "__main__":
    json_string = input()
    easyrider = EasyRider(json_string)

    easyrider.check_on_demands_stop()