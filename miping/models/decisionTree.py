from sklearn import tree


class DecisionTree:
    """
    TODO docstring Class DecisionTree
    """

    def __init__(
        self,
        gridSearchParams=None,
    ):
        """
        TODO init func Class DecisionTree
        gridSearchParams: dict
        """

        if gridSearchParams is not None:
            self.gridSearchParams = gridSearchParams
        else:
            # TODO applying best default parameters
            defaultParams = {
                'criterion': ['mse'],
                'splitter': ['best'],
                'max_depth': [10],
                'min_samples_split': [2],
                'min_samples_leaf': [1],
                'random_state': [0]
            }

            self.gridSearchParams = defaultParams

        self.name = 'DecisionTree'

        return

    def getModel(
        self,
    ):
        """
        TODO func getModel
        returns default model
        this will be modified during gridsearch
        """

        model = tree.DecisionTreeRegressor()

        return model
