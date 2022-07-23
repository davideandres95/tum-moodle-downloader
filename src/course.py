import re

from bs4 import BeautifulSoup

import globals
from resource import Resource


class Course:
    def __init__(self, course_name, course_url):
        self.name = course_name

        course_page = globals.global_session.get(course_url).content
        self.soup = BeautifulSoup(course_page, 'html.parser')

        self.resources = {}
        self._extract_resources()
        self.latest_resources = [resource for resource in self.resources.values() if resource.is_recent]

    def _add_resource(self, resource, week):
        if resource.name in self.resources:
            self.resources[resource.name+" "+week] = resource
        else:
            self.resources[resource.name] = resource

    def _extract_resources(self):
        sections = []
        latest_week_section = None

        # Extract sections for courses structured by weeks
        weeks = self.soup.find('ul', class_='weeks')
        if weeks is not None:
            sections += weeks.find_all('li', class_='section main clearfix')  # All week secation
            latest_week_section = weeks.find('li', class_='section main clearfix current')
            if latest_week_section is not None:
                sections.append(latest_week_section)

        # Extract sections for courses structured by topics
        topics = self.soup.find('ul', class_='topics')
        if topics is not None:
            sections += topics.find_all('li', class_='section main clearfix')  # All topic sections

        # Extract resources from the sections
        for section in sections:
            week_name = section.find('h3', class_="sectionname").find('span').getText()
            section_resources = section.find_all('div', class_='activityinstance')
            for resource_div in section_resources:
                resource = Resource(resource_div, is_recent=(section == latest_week_section), week= week_name)
                self._add_resource(resource, week_name)

            section_resources = section.find_all('div', class_='contentwithoutlink')
            for resource_div in section_resources:
                for label in resource_div.find_all('a'):
                    resource = Resource(label, is_recent=(section == latest_week_section), week = week_name)
                    self._add_resource(resource, week_name)

    def download_resource(self, resource_name, destination_dir, update_handling):
        """
            Downloads the course resource with the requested name 'resource_name' to the path 'destination_dir'.
            The specified 'update_handling' is applied, if the file already exists.
            Currently supports files, folders and assignments.
        """
        try:
            print(f'Searching for resource {resource_name} in course {self.name} ...')
            resource = self.resources.get(resource_name, None)
            if resource is None:
                print(f'No resource matching {resource_name} found')
            else:
                resource.download(destination_dir, update_handling)
        except:
            # TODO: add logging and log exception info (traceback to a file)
            print(f"Could not download any resource matching {resource_name} due to an internal error.")

    def download_latest_resources(self, destination_dir, update_handling):
        print(f'Downloading latest resources for course {self.name} ...\n')
        if len(self.latest_resources) == 0:
            print('No resources categorized as "latest" found.')
        for resource in self.latest_resources:
            resource.download(destination_dir, update_handling)

    def list_all_resources(self):
        print(f'Listing all available resources for course {self.name} ...\n')
        for name, resource in self.resources.items():
            # TODO: check, check if resource is actually available for the user
            #  (see: https://github.com/NewLordVile/tum-moodle-downloader/issues/11)
            print(f"{name} ---- type: {resource.type}")

    def list_latest_resources(self):
        print('Listing latest resources ...\n')
        if len(self.latest_resources) == 0:
            print('No resources categorized as "latest" found.')
        for resource in self.latest_resources:
            print(f"{resource.name} ---- type: {resource.type}")

    def get_matching_resource_names(self, resource_pattern=".*"):
        resource_pattern = re.compile(resource_pattern)
        resource_names = []
        for name, resource in self.resources.items():
            if re.match(resource_pattern, resource.name):
                resource_names.append(resource.name)
        return resource_names
