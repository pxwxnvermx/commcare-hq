from corehq.apps.app_manager.dbaccessors import wrap_app
from corehq.apps.app_manager.management.commands.helpers import AppMigrationCommandBase
from corehq.apps.domain.models import Domain
import random


def get_new_case_update_json(name_path):
    return {
        'question_path': name_path,
        'update_mode': 'always'
    }


class Command(AppMigrationCommandBase):
    help = """
    One-time migration to transition form action models to use ConditionalCaseUpdate as part of the new
    "save only if edited" feature: https://github.com/dimagi/commcare-hq/pull/30910.
    """

    include_linked_apps = True
    include_builds = True
    DOMAIN_LIST_FILENAME = "migrate_to_cond_case_update_cmd_domain_list.txt"
    DOMAIN_PROGRESS_NUMBER_FILENAME = "migrate_to_cond_case_update_cmd_domain_progress.txt"

    def add_arguments(self, parser):
        super().add_arguments(parser)

        # Used for a dry run on 1000 domains to get a taste of how long a full migration would take.
        parser.add_argument(
            '--num-domains-test',
            action='store',
            default=None,
            help='''For a dry run, use this argument to test on X number of domains. Dry run flag must be
                    included and domain flag cannot be included.''',
        )

    def _has_been_migrated(self, app_doc):
        for module in app_doc['modules']:
            for form in module['forms']:
                if module['module_type'] == "basic":
                    actions = form.get('actions', '')
                    if actions:
                        open_case_action = actions.get('open_case', '')
                        if open_case_action:
                            if (open_case_action.get('name_update', '')
                            and not open_case_action.get('name_path', '')):
                                return True
                            if open_case_action.get('name_path', ''):
                                return False
                elif module['module_type'] == "advanced":
                    for form in module['forms']:
                        if form['form_type'] == 'advanced_form':
                            actions = form.get('actions', '')
                            if actions:
                                open_case_action = actions.get('open_cases', '')[0] \
                                    if actions.get('open_cases', '') else None
                                if open_case_action:
                                    if (open_case_action.get('name_update', '')
                                    and not open_case_action.get('name_path', '')):
                                        return True
                                    if open_case_action.get('name_path', ''):
                                        return False
        # Catch-all; if it's all surveys or something else strange, migrate it by default
        return False

    def migrate_app(self, app_doc):
        if self._has_been_migrated(app_doc):
            return None
        else:
            return wrap_app(app_doc)

    @property
    def num_domains_test(self):
        return self.options.get('num_domains_test', None)

    def get_domains(self):
        if self.is_dry_run and self.num_domains_test:
            print(self.num_domains_test)
            all_domain_names = Domain.get_all_names()
            random.shuffle(all_domain_names)
            return all_domain_names[:int(self.num_domains_test)]
        else:
            return Domain.get_all_names()
